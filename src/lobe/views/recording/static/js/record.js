/*
In this file the recording functionality is implemented.

The recording is done using RecorderRTC, which implements a lossless audio recorder, across all browsers.

The flow in the UI is as follows:
1. The page loads and the user is presented with the first sentence to record.
2. a) The user clicks the "byrja/record" button and the recording starts. (given that the user has given permission to use the microphone)
At this point the user cannot:
- Go to the next sentence.
- Go to the previous sentence.
- Skip the sentence.
2. b) The user clicks the "sleppa/skip" button to skip the sentence.
3. The user clicks the "byrja/record" button again (now labelled as "stoppa") to stop the recording.
At this point the user can:
- Listen to the recording by clicking the play button.
- Delete the recording by clicking the delete button.
- Cut the recording by clicking the cut button.
4. The user can click the next button to go to the next sentence. The recording is not uploaded to the server until the user clicks the "klára" button.
5. A new sentence is presented to the user.





*/
"use strict";
window.onbeforeunload = function () {
  return "Are you sure?";
};

let mediaRecorder;
let audioCtx;
let ws;
let micSurfer;
let wavesurfer;
let stream;
let meter;

// ----------------- Constants -----------------
// Audio configuration
// We only support mono audio, not video
// For more information about the constraints, see:
// https://developer.mozilla.org/en-US/docs/Web/API/MediaTrackConstraints
const mediaConstraints = {
  audio: {
    sampleRate: 48000, // Not supported in Firefox
    sampleSize: 16, // Not supported in Firefox
    channelCount: 1,
    echoCancellation: true,
    autoGainControl: true, // not supported on Safari, desktop and mobile
    noiseSuppression: true, // not supported on Safari, desktop and mobile
    latency: 0,
  },
};
// RecorderRTC configuration
const mediaRecorderConfig = {
  type: "audio",
  mimeType: "audio/wav",
  recorderType: StereoAudioRecorder,
  sampleRate: mediaConstraints.audio.sampleRate,
  bufferSize: 4096,
  numberOfAudioChannels: mediaConstraints.audio.channelCount,
  disableLogs: true,
};
// For more information about the supported constraints, see:
// https://developer.mozilla.org/en-US/docs/Web/API/MediaTrackSupportedConstraints
const supportedConstraints = navigator.mediaDevices.getSupportedConstraints();
console.log("Supported constraints: ", supportedConstraints);

// ----------------- Application state -----------------
var tokenIndex = 0; // At what utterance are we now?
var numTokens = tokens.length;

// ----------------- UI elements -----------------
//token stuff
const tokenText = document.querySelector("#tokenText");
const tokenIDSpan = document.querySelector("#tokenID");
const tokenHref = document.querySelector("#tokenHref");
const tokenfileIDSpan = document.querySelector("#tokenFileID");
const tokenProgress = document.querySelector("#tokenProgress");
const currentIndexSpan = document.querySelector("#currentIndexSpan");
const totalIndexSpan = document.querySelector("#totalIndexSpan");
const tokenCard = document.querySelector("#tokenCard");
const videoCard = document.querySelector("#videoCard");

//recording
const recordButtonText = document.querySelector("#recordButtonText");
const recordingCard = document.querySelector("#recordingCard");
const micCard = document.querySelector("#micCard");

//analyze
const analyzeListElement = document.querySelector("li#analyzeLi");
const analyzeMsgElement = document.querySelector("span#analyzeMsg");
const analyzeIcn = document.querySelector("#analyzeIcn");

//buttons
const recordButton = document.querySelector("button#record");
const nextButton = document.querySelector("button#next");
const prevButton = document.querySelector("button#prev");
const deleteButton = document.querySelector("button#delete");
const playButton = document.querySelector("button#play");
const skipButton = document.querySelector("button#skip");
const downloadButton = document.querySelector("button#download");
const finishButton = document.querySelector("button#send");
const finishButtonIcon = $("#finishButtonIcon");
const cutButton = document.querySelector("button#cut");
const cutButtonIcon = document.querySelector("#cutButtonIcon");
const cutButtonText = document.querySelector("#cutButtonText");

//other
if (conf.has_video) {
  const videoPlaceHolder = document.querySelector("#videoPlaceHolder");
  const liveVideo = document.querySelector("#liveVideo");
  let recordedVideo = document.querySelector("#recordedVideo");
  recordedVideo.controls = false;
}
const downloadRecordFName = document.querySelector("code#downloadRecordFName");

const startTime = new Date();

//meter
var meterCanvas = document.querySelector("#meter");
var canvasContext = meterCanvas.getContext("2d");
var rafID = null;

// Audio configuration
// We only support mono audio, not video
const mediaConstraints = {
  audio: {
    sampleRate: 48000,
    sampleSize: 16,
    numChannels: 1,
    echoCancellation: true,
  },
};
// RecorderRTC configuration
const mediaRecorderConfig = {
  type: "audio",
  mimeType: "audio/wav",
  recorderType: StereoAudioRecorder,
  sampleRate: 48000,
  bufferSize: 4096,
  numberOfAudioChannels: 1,
};

// ------------- register listeners ------------
nextButton.addEventListener("click", nextAction);
prevButton.addEventListener("click", prevAction);
recordButton.addEventListener("click", recordAction);
playButton.addEventListener("click", playAction);
deleteButton.addEventListener("click", deleteAction);
skipButton.addEventListener("click", skipAction);
downloadButton.addEventListener("click", downloadAction);
finishButton.addEventListener("click", finishAction);
cutButton.addEventListener("click", cutAction);
$(window).keyup(function (e) {
  if (
    e.key === " " ||
    e.key === "Spacebar" ||
    e.keyCode === 38 ||
    e.keyCode === 87
  ) {
    // spacebar, arrow-up or "w"
    e.preventDefault();
    recordAction();
  } else if (e.keyCode === 37 || e.keyCode === 65) {
    // arrow-left or "a"
    prevAction();
  } else if ((e.keyCode === 39 || e.keyCode === 68) && !nextButton.disabled) {
    // arrow-right or "d"
    nextAction();
  } else if (e.keyCode === 40 || e.keyCode === 83) {
    // arrow-down or "s"
    playAction();
  }
});

// ---------------- Actions --------------------
async function nextAction() {
  // Increment the sentence index and update the UI
  if (tokenIndex < numTokens - 1) {
    tokenIndex += 1;
    await updateUI(tokenIndex);
  } else {
    finishAction();
  }
}

async function prevAction() {
  // Decrement the sentence index and update the UI
  if (tokenIndex > 0) {
    tokenIndex -= 1;
    await updateUI(tokenIndex);
  }
}

async function recordAction() {
  if (!(await areRecording())) {
    if ("recording" in tokens[tokenIndex]) {
      deleteAction();
    }
    await startRecording();
    tokenCard.style.borderWidth = "2px";
    tokenCard.classList.add("border-success");
    skipButton.disabled = true;
    nextButton.disabled = true;
    prevButton.disabled = true;
    recordButtonText.innerHTML = "Stoppa";
  } else {
    await stopRecording();
    tokenCard.classList.remove("border-success");
    tokenCard.style.borderWidth = "1px";
    recordButtonText.innerHTML = "Byrja";
    skipButton.disabled = false;
    nextButton.disabled = false;
    prevButton.disabled = false;
  }
}

function deleteAction() {
  delete tokens[tokenIndex].recording;
  updateUI(tokenIndex);
}

async function skipAction() {
  // mark as skipped
  if ("skipped" in tokens[tokenIndex]) {
    // reverse from marking as skipped
    delete tokens[tokenIndex].skipped;
    updateUI(tokenIndex);
  } else {
    tokens[tokenIndex].skipped = true;
    // then go to next
    if ("recording" in tokens[tokenIndex]) {
      delete tokens[tokenIndex].recording;
    }
    await nextAction();
  }
}

function playAction() {
  // Play the recording for the sentence at the current index.

  if (arePlaying()) {
    wavesurfer.pause();
  } else {
    if (
      Object.keys(wavesurfer.regions) &&
      Object.keys(wavesurfer.regions.list).length > 0
    ) {
      wavesurfer.regions.list[Object.keys(wavesurfer.regions.list)[0]].play();
    } else {
      wavesurfer.play();
    }
  }
}

function downloadAction() {
  const a = document.createElement("a");
  a.style.display = "none";
  a.href = tokens[tokenIndex].recording.url;
  a.download = tokens[tokenIndex].recording.fname;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

function finishAction() {
  finishButtonIcon
    .removeClass("fa-arrow-right")
    .addClass("fa-spinner")
    .addClass("fa-spin");
  var xhr = new XMLHttpRequest();
  xhr.onload = function (e) {
    if (this.readyState === XMLHttpRequest.DONE) {
      finishButtonIcon.removeClass("fa-spinner").removeClass("fa-spin");
      if (xhr.status == "200") {
        // if we finish we go straight to the session
        var session_url = xhr.responseText;
        finishButtonIcon.addClass("fa-check");

        window.onbeforeunload = null;
        window.location = session_url;
      } else {
        finishButtonIcon.addClass("fa-times");
        finishButton.classList.add("btn-danger");
        promptError(
          "Villa koma upp við að senda upptökur",
          xhr.responseText,
          ""
        );
      }
    }
    finishButton.disabled = true;
  };
  var fd = new FormData();
  var recordings = {};
  var skipped = [];
  fd.append(
    "duration",
    JSON.stringify((new Date().getTime() - startTime.getTime()) / 1000)
  );
  fd.append("user_id", user_id);
  fd.append("manager_id", manager_id);
  fd.append("collection_id", collection_id);
  for (var i = 0; i < numTokens; i++) {
    if ("recording" in tokens[i]) {
      recordings[tokens[i].id] = tokens[i].recording;
      if ("analysis" in tokens[i]) {
        recordings[tokens[i].id].analysis = tokens[i].analysis;
      }
      if ("cut" in tokens[i]) {
        recordings[tokens[i].id].cut = {
          start: tokens[i].cut.start,
          end: tokens[i].cut.end,
        };
      }
      fd.append(
        "file_" + tokens[i].id,
        tokens[i].recording.blob,
        tokens[i].recording.fname
      );
    } else if (tokens[i].skipped) {
      // append as skipped
      skipped.push(tokens[i]["id"]);
    }
  }
  fd.append("recordings", JSON.stringify(recordings));
  fd.append("skipped", JSON.stringify(skipped));
  xhr.open("POST", postRecordingRoute, true);
  xhr.send(fd);
}

function cutAction() {
  if (Object.keys(wavesurfer.regions.list).length > 0) {
    if ("cut" in tokens[tokenIndex]) {
      delete tokens[tokenIndex].cut;
      wavesurfer.clearRegions();
    } else {
      var region =
        wavesurfer.regions.list[Object.keys(wavesurfer.regions.list)[0]];
      tokens[tokenIndex].cut = region;
    }
  }
  setCutUI();
}

// ---------------- Functions --------------------
async function areRecording() {
  if (mediaRecorder) {
    return (await mediaRecorder.getState()) === "recording";
  }
  return false;
}

async function startRecording() {
  if (!!wavesurfer) {
    wavesurfer.destroy();
  }
  try {
    stream = await navigator.mediaDevices.getUserMedia(mediaConstraints);
    mediaRecorder = new RecordRTCPromisesHandler(stream, mediaRecorderConfig);
    // Start recording
    mediaRecorder.startRecording();
    if (conf.visualize_mic) {
      setMicUI(true, stream);
    }
  } catch (e) {
    console.log(e);
    if (e instanceof OverconstrainedError) {
      promptError(
        `Villa kom upp í Media Constraints. Of hátt gildi á ${e.constraint}`,
        e.message,
        e.stack
      );
    }
  }
}

async function stopRecording() {
  // read information about the audio track - we send this to the server
  let audioTrack = stream.getAudioTracks()[0];
  // See: https://developer.mozilla.org/en-US/docs/Web/API/MediaTrackSettings
  let audioSettings = audioTrack.getSettings();

  await mediaRecorder.stopRecording();
  let blob = await mediaRecorder.getBlob();
  tokens[tokenIndex].recording = {
    blob: blob,
    fname: `${new Date().toISOString()}.wav`,
    url: URL.createObjectURL(blob),
    settings: {
      sampleRate: audioSettings.sampleRate || mediaConstraints.audio.sampleRate, // not in audioSettings in Firefox
      sampleSize: audioSettings.sampleSize || mediaConstraints.audio.sampleSize, // not in audioSettings in Firefox
      channelCount: mediaConstraints.audio.channelCount, // never in audioSettings
      latency: audioSettings.latency || mediaConstraints.audio.latency, // only is Safari
      autoGainControl: audioSettings.autoGainControl || false,
      echoCancellation: audioSettings.echoCancellation,
      noiseSuppression: audioSettings.noiseSuppression || false,
    },
  };
  console.log("Recording stored (not sent):");
  console.log(tokens[tokenIndex].recording);

  if (conf.visualize_mic) {
    setMicUI(false, stream);
  }

  //stop mediadevice access
  stream.getTracks().forEach((track) => track.stop());
  stream = null;
  // reset mediaRecorder
  await mediaRecorder.reset();
  await mediaRecorder.destroy();
  mediaRecorder = null;

  await setRecordingUI(tokenIndex);
}
// ---------------- UI configuration --------------------
async function updateUI(tokenIndex) {
  setTokenUI(tokenIndex);
  setProgressUI(tokenIndex + 1);
  setSkipButtonUI(tokenIndex);
  setAnalysisUI(tokenIndex);
  await setRecordingUI(tokenIndex);
  setCutUI();
}

async function setVideoUI() {
  if (areRecording()) {
    videoPlaceHolder.style.display = "none";
    liveVideo.style.display = "block";
    recordedVideo.style.display = "none";
    videoCard.style.display = "block";
  } else if ("recording" in tokens[tokenIndex]) {
    videoPlaceHolder.style.display = "none";
    liveVideo.style.display = "none";
    recordedVideo.src = window.URL.createObjectURL(
      tokens[tokenIndex].recording.blob
    );
    recordedVideo.style.display = "block";
    videoCard.style.display = "block";
  } else {
    videoPlaceHolder.style.display = "inline-block";
    videoCard.style.display = "none";
  }
}
function setProgressUI(i) {
  var ratio = (i / numTokens) * 100;
  tokenProgress.style.width = `${ratio.toString()}%`;
}

function setCutUI(newRegion = false) {
  if (newRegion || (wavesurfer && areRegions())) {
    cutButton.disabled = false;
    if ("cut" in tokens[tokenIndex]) {
      cutButtonIcon.classList.remove("text-success");
      cutButtonIcon.classList.add("text-danger");
      cutButtonText.innerHTML = "Afklippa";
    } else {
      cutButtonIcon.classList.remove("text-danger");
      cutButtonIcon.classList.add("text-success");
      cutButtonText.innerHTML = "Klippa";
    }
  } else {
    cutButtonIcon.classList.remove("text-danger");
    cutButtonIcon.classList.add("text-success");
    cutButtonText.innerHTML = "Klippa";
    cutButton.disabled = true;
  }
}

function setTokenUI(tokenIndex) {
  // Set the token text, file ID and URL
  // This should be called whenever the tokenIndex changes
  tokenText.innerHTML = tokens[tokenIndex]["text"];
  tokenfileIDSpan.innerHTML = tokens[tokenIndex]["file_id"];
  tokenHref.href = tokens[tokenIndex]["url"];
  currentIndexSpan.innerHTML = tokenIndex + 1;
}

function setSkipButtonUI(tokenIndex) {
  // Set the skip button style and whether it is disabled
  // This should be called whenever the tokenIndex changes or when the skip button is pressed
  if (tokens[tokenIndex].skipped) {
    skipButton.classList.remove("text-danger", "btn-secondary");
    skipButton.classList.add("btn-danger");
    // also disable the recording button
    recordButton.disabled = true;
  } else {
    skipButton.classList.remove("btn-danger");
    skipButton.classList.add("text-danger", "btn-secondary");
    recordButton.disabled = false;
  }
}

async function setRecordingUI(tokenIndex) {
  // if it has a recording we show the recording card
  // This should be called whenever the tokenIndex changes and when a recording is made
  if ("recording" in tokens[tokenIndex]) {
    if (typeof wavesurfer === "object") {
      wavesurfer.destroy();
    }
    wavesurfer = createWaveSurfer(
      "#waveform",
      conf.has_video,
      playButtonIcon,
      nextButton,
      prevButton,
      recordButton,
      skipButton,
      deleteButton
    );
    if (conf.has_video) {
      await wavesurfer.load(recordedVideo);
    } else {
      await wavesurfer.loadBlob(tokens[tokenIndex].recording.blob);
    }
    if ("cut" in tokens[tokenIndex]) {
      wavesurfer.addRegion({
        ...tokens[tokenIndex].cut,
        ...{ color: "rgba(243, 156, 18, 0.1)" },
      });
    }
    downloadRecordFName.innerHTML = tokens[tokenIndex].recording.fname;
    recordingCard.style.display = "block";
  } else {
    recordingCard.style.display = "none";
  }
}

function setAnalysisUI(tokenIndex) {
  if ("recording" in tokens[tokenIndex] && !conf.analyze_sound) {
    setAnalyzeElement(
      "Slökkt er á gæðastjórnun",
      "warning",
      "fa-question-circle"
    );
  } else if (
    "recording" in tokens[tokenIndex] &&
    "analysis" in tokens[tokenIndex]
  ) {
    switch (tokens[tokenIndex].analysis) {
      case "ok":
        setAnalyzeElement("Upptaka er góð", "success", "fa-thumbs-up");
        break;
      case "high":
        setAnalyzeElement("Upptaka of há", "danger", "fa-thumbs-down");
        break;
      case "low":
        setAnalyzeElement("Upptaka of lág", "danger", "fa-thumbs-down");
        break;
      case "error":
        setAnalyzeElement("Villa kom upp", "danger", "fa-times");
        break;
    }
  } else {
    analyzeListElement.style.display = "none";
  }

  function setAnalyzeElement(text, type, icon) {
    analyzeListElement.style.display = "block";
    analyzeMsgElement.textContent = text;
    analyzeMsgElement.classList.remove(
      "text-success",
      "text-danger",
      "text-warning"
    );
    analyzeMsgElement.classList.add(`text-${type}`);
    analyzeIcn.classList.remove(
      "fa-thumbs-up",
      "fa-thumbs-down",
      "fa-times",
      "fa-question",
      "text-success",
      "text-danger",
      "text-warning"
    );
    analyzeIcn.classList.add(icon, `text-${type}`);
  }
}

async function setMicUI(recording, stream) {
  // if we are recording we show the mic card
  if (recording) {
    let clonedStream = stream.clone();
    audioCtx = new AudioContext(clonedStream);
    meter = createMeter(audioCtx, clonedStream);
    meterDrawLoop();
    micSurfer = createMicSurfer(audioCtx, "#micWaveform");
    micSurfer.microphone.start();
    micCard.style.display = "block";
  } else {
    micCard.style.display = "none";
    meter.shutdown();
    micSurfer.microphone.stop();
    micSurfer.destroy();
    await audioCtx.close();
  }
}

// ----------------- Other -----------------
function arePlaying() {
  if (wavesurfer) {
    return wavesurfer.isPlaying();
  }
  return false;
}

function areRegions() {
  return (
    typeof wavesurfer === "object" &&
    Object.keys(wavesurfer.regions.list).length > 0
  );
}

async function analyze() {
  var body = await JSON.parse(analyzeAudio(recordedBlobs, analyze_url, conf));
  tokens[tokenIndex].cut = body.segment;
  tokens[tokenIndex].analysis = body.analysis;
}

// --------------------- Initialize UI --------------------------
totalIndexSpan.innerHTML = numTokens;
updateUI(0);

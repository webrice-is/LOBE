import datetime
import json
import random
import traceback
from datetime import date, datetime, timedelta

from flask import Blueprint, Response
from flask import current_app as app
from flask import flash, redirect, render_template, request, url_for
from flask_security import current_user, login_required, roles_accepted
from sqlalchemy import and_, or_

from lobe.database_functions import activity, get_verifiers, insert_trims, resolve_order
from lobe.forms import DeleteVerificationForm, SessionVerifyForm
from lobe.models import (
    Collection,
    PrioritySession,
    Recording,
    Session,
    User,
    Verification,
    db,
)

verification = Blueprint("verification", __name__, template_folder="templates")


@verification.route("/verification/verify_queue")
@login_required
def verify_queue():
    """
    Finds the oldest and unverified session and redirects
    to that session verification. The session must either
    be assigned to the current user id or no user id
    """

    """
    First checks if there are any priority sessions,
    then it uses the following list to priorities 
    those available. 

    Logic of queue priority:
    1. Check if there are sessions that are not verified
    2. Check if any are not assigned to other users
    3. Check if any are not secondarily verified
    4. Check if any of those are not assigned to other users
    """

    chosen_session = None
    is_secondary = False
    priority_session = None
    normal_session = True
    # priority_session, is_secondary, normal_session = check_priority_session()
    if priority_session:
        chosen_session = priority_session
    else:
        # Has the user already started a session?
        unverified_sessions = Session.query.join(Session.collection).filter(
            Session.is_verified is False,
            Collection.is_dev is False,
            Collection.verify is True,
        )
        if unverified_sessions.count() > 0:
            available_sessions = unverified_sessions.filter(
                or_(Session.verified_by is None, Session.verified_by == current_user.id)
            ).order_by(Session.verified_by)

            if available_sessions.count() > 0:
                # We have available sessions
                if available_sessions[0].verified_by == current_user.id:
                    chosen_session = available_sessions[0]
                else:
                    random_session_index = random.randrange(available_sessions.count())
                    chosen_session = available_sessions[random_session_index]
                    chosen_session.verified_by = current_user.id

        if chosen_session is None:
            # check if we can secondarily verify any sesssions
            secondarily_unverified_sessions = Session.query.join(Session.collection).filter(
                and_(
                    Session.is_secondarily_verified is False,
                    Session.verified_by != current_user.id,
                ),
                Collection.is_dev is False,
                Collection.verify is True,
            )

            if secondarily_unverified_sessions.count() > 0:
                available_sessions = secondarily_unverified_sessions.filter(
                    or_(
                        Session.secondarily_verified_by is None,
                        Session.secondarily_verified_by == current_user.id,
                    )
                ).order_by(Session.secondarily_verified_by)

                if available_sessions.count() > 0:
                    # we have an available session
                    is_secondary = True
                    if available_sessions[0].secondarily_verified_by == current_user.id:
                        chosen_session = available_sessions[0]
                    else:
                        random_session_index = random.randrange(available_sessions.count())
                        chosen_session = available_sessions[random_session_index]
                        chosen_session.secondarily_verified_by = current_user.id

    if chosen_session is None:
        # there are no sessions left to verify
        flash("Engar lotur eftir til að greina", category="warning")
        return redirect(url_for("verification.verify_index"))

    # Once queued, a session is assigned to a user id to avoid
    # double queueing
    db.session.commit()
    url = url_for("verification.verify_session", id=chosen_session.id)
    if is_secondary:
        url = url + "?is_secondary={}".format(is_secondary)
    if priority_session and not normal_session:
        url = url + "?is_priority={}".format(True)
    return redirect(url)


def check_priority_session():
    unverified_sessions = PrioritySession.query.filter(
        and_(PrioritySession.is_verified is False, PrioritySession.is_dev is False)
    )
    chosen_session = None
    is_secondary = False
    normal_session = False
    if unverified_sessions.count() > 0:
        available_sessions = unverified_sessions.filter(
            or_(
                PrioritySession.verified_by is None,
                PrioritySession.verified_by == current_user.id,
            )
        ).order_by(PrioritySession.verified_by)

        if available_sessions.count() > 0:
            # we have an available session
            chosen_session = available_sessions[0]
            chosen_session.verified_by = current_user.id

    if not chosen_session:
        unverified_sessions = Session.query.filter(
            and_(
                Session.is_verified is False,
                Session.is_dev is False,
                Session.has_priority is True,
            )
        )
        if unverified_sessions.count() > 0:
            available_sessions = unverified_sessions.filter(
                or_(Session.verified_by is None, Session.verified_by == current_user.id)
            ).order_by(Session.verified_by)
            if available_sessions.count() > 0:
                # we have an available session
                chosen_session = available_sessions[0]
                chosen_session.verified_by = current_user.id
                normal_session = True
    db.session.commit()

    return chosen_session, is_secondary, normal_session


@verification.route("/sessions/<int:id>/verify/")
@login_required
def verify_session(id):
    is_secondary = bool(request.args.get("is_secondary", False))
    is_priority = bool(request.args.get("is_priority", False))
    form = SessionVerifyForm()
    if is_priority:
        session = PrioritySession.query.get(id)
        session_dict = {
            "id": session.id,
            "is_secondary": is_secondary,
            "recordings": [],
        }
    else:
        session = Session.query.get(id)
        session_dict = {
            "id": session.id,
            "collection_id": session.collection.id,
            "is_secondary": is_secondary,
            "recordings": [],
        }
    for recording in session.recordings:
        # make sure we only verify recordings that haven't been verified
        # two times
        if (not recording.is_verified and not is_secondary) or (not recording.is_secondarily_verified and is_secondary):
            session_dict["recordings"].append(
                {
                    "rec_id": recording.id,
                    "rec_fname": recording.fname,
                    "rec_url": recording.get_download_url(),
                    "rec_num_verifies": len(recording.verifications),
                    "text": recording.token.text,
                    "text_file_id": recording.token.fname,
                    "text_url": recording.token.get_url(),
                    "token_id": recording.token.id,
                }
            )

            if recording.is_verified:
                # add the verification object
                session_dict["recordings"][-1]["verification"] = recording.verifications[0].dict

    return render_template(
        "verify_session.jinja",
        session=session,
        form=form,
        isPriority=is_priority,
        delete_form=DeleteVerificationForm(),
        json_session=json.dumps(session_dict),
        is_secondary=is_secondary,
    )


@verification.route("/verifications", methods=["GET"])
@login_required
def verification_list():
    page = int(request.args.get("page", 1))

    verifications = Verification.query.order_by(
        resolve_order(
            Verification,
            request.args.get("sort_by", default="created_at"),
            order=request.args.get("order", default="desc"),
        )
    ).paginate(page=page, per_page=app.config["VERIFICATION_PAGINATION"])

    return render_template("verification_list.jinja", verifications=verifications, section="verification")


@verification.route("/verifications/all/", methods=["GET"])
@login_required
def download_verifications():
    verifications = Verification.query.all()
    response_lines = [verification.as_tsv_line() for verification in verifications]
    r = Response(response="\n".join(response_lines), status=200, mimetype="text/plain")
    r.headers["Content-Type"] = "text/plain; charset=utf-8"
    return r


@verification.route("/verifications/<int:id>/")
@login_required
def verification_detail(id):
    verification = Verification.query.get(id)
    delete_form = DeleteVerificationForm()

    return render_template(
        "verification.jinja",
        verification=verification,
        delete_form=delete_form,
        section="verification",
    )


@verification.route("/verifications/create/", methods=["POST"])
@login_required
def create_verification():
    form = SessionVerifyForm(request.form)
    try:
        if form.validate():
            is_priority = form.data["isPriority"] == "True"
            is_secondary = int(form.data["num_verifies"]) > 0
            verification = Verification()
            verification.set_quality(form.data["quality"])
            verification.comment = form.data["comment"]
            verification.recording_id = int(form.data["recording"])
            verification.is_secondary = is_secondary
            verification.verified_by = int(form.data["verified_by"])
            db.session.add(verification)
            db.session.flush()
            verification_id = verification.id
            db.session.commit()
            recording = Recording.query.get(int(form.data["recording"]))
            if is_secondary:
                recording.is_secondarily_verified = True
                recording.is_verified = True  # Sometimes this is missing for some reason
            else:
                recording.is_verified = True
            db.session.commit()

            insert_trims(form.data["cut"], verification_id)

            # check if this was the final recording to be verified and update
            if is_priority:
                session = PrioritySession.query.get(int(form.data["session"]))
            else:
                session = Session.query.get(int(form.data["session"]))
            recordings = Recording.query.filter(Recording.session_id == session.id)
            num_recordings = recordings.count()
            if is_secondary and num_recordings == recordings.filter(Recording.is_secondarily_verified is True).count():
                session.is_secondarily_verified = True
                db.session.commit()
            if num_recordings == recordings.filter(Recording.is_verified is True).count():
                session.is_verified = True
                db.session.commit()

            db.session.commit()

            return Response(json.dumps(response), status=200)
        else:
            errorMessage = "<br>".join(
                list("{}: {}".format(key, ", ".join(value)) for key, value in form.errors.items())
            )
            return Response(errorMessage, status=500)
    except Exception as error:
        app.logger.error("Error creating a verification : {}\n{}".format(error, traceback.format_exc()))


@verification.route("/verifications/delete", methods=["POST"])
@login_required
def delete_verification():
    form = DeleteVerificationForm(request.form)
    if form.validate():
        verification = Verification.query.get(int(form.data["verification_id"]))
        is_secondary = verification.is_secondary
        recording = Recording.query.get(verification.recording_id)
        session = Session.query.get(recording.session_id)

        if is_secondary:
            recording.is_secondarily_verified = False
            session.is_secondarily_verified = False
        else:
            recording.is_verified = False
            session.is_verified = False
        db.session.delete(verification)
        db.session.commit()

        return Response(json.dumps(response), status=200)
    else:
        errorMessage = "<br>".join(list("{}: {}".format(key, ", ".join(value)) for key, value in form.errors.items()))
        return Response(errorMessage, status=500)


@verification.route("/verification", methods=["GET"])
@login_required
def verify_index():
    """
    Home screen of the verifiers
    """
    verifiers = get_verifiers()
    verification_progress = 0

    activity_days, activity_counts = activity(Verification)
    # show_weekly_prices, show_daily_spin = False, False #disable prizes when not in use

    # get the number of verifications per user
    return render_template(
        "verify_index.jinja",
        verifiers=verifiers,
        verification_progress=verification_progress,
        activity_days=activity_days,
        activity_counts=activity_counts,
    )



@verification.route("/verification/stats", methods=["GET"])
@login_required
@roles_accepted("admin")
def verify_stats():
    """
    Statistics screen of the verifiers
    """
    verifiers = get_verifiers()

    verifications = Verification.query
    verifications_all = verifications.all()
    verify_stats = {
        "total_count": len(verifications_all),
        "double_verified": verifications.filter(Verification.is_secondary is True).count(),
        "single_verified": verifications.filter(Verification.is_secondary is False).count(),
        "count_past_week": verifications.filter(Verification.created_at >= datetime.now() - timedelta(days=7)).count(),
        "count_good": verifications.filter(
            and_(
                Verification.volume_is_low is False,
                Verification.volume_is_high is False,
                Verification.recording_has_wrong_wording is False,
                Verification.recording_has_glitch is False,
            )
        ).count(),
        "count_bad": verifications.filter(
            or_(
                Verification.volume_is_low is True,
                Verification.volume_is_high is True,
                Verification.recording_has_wrong_wording is True,
                Verification.recording_has_glitch is True,
            )
        ).count(),
    }
    from_arg = request.args.get("from")
    to_arg = request.args.get("to")
    if valid_dates([from_arg, to_arg]):
        custon_dates = Verification.query.filter(db.func.date(Verification.created_at).between(from_arg, to_arg))
        date_selection = {
            "from": from_arg,
            "to": to_arg,
            "number": custon_dates.count(),
        }
        verify_stats["date_selection"] = date_selection

    activity_days, activity_counts = activity(Verification)

    return render_template(
        "verify_stats.jinja",
        verifiers=verifiers,
        verify_stats=verify_stats,
        activity_days=activity_days,
        activity_counts=activity_counts,
    )


def valid_dates(dates):
    if len(dates) != 2 or None in dates:
        return False

    new_dates = []
    for d in dates:
        try:
            new_dates.append(datetime.strptime(d, "%Y-%m-%d"))
        except ValueError:
            return False
            # raise ValueError("Dagsetning ekki á réttu formi, ætti að vera: YYYY-MM-DD")
    if sorted(dates) == dates:
        return True
    return False

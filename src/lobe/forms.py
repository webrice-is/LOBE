from flask_security.forms import RegisterForm
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import (
    BooleanField,
    EmailField,
    FloatField,
    HiddenField,
    IntegerField,
    MultipleFileField,
    SelectField,
    SelectMultipleField,
    StringField,
    ValidationError,
    widgets,
)
from wtforms.validators import InputRequired, NumberRange
from wtforms_alchemy import model_form_factory
from wtforms_alchemy.fields import QuerySelectField
from markupsafe import Markup

from lobe import db
from lobe.models import (
    Configuration,
    Mos,
    MosInstance,
    Posting,
    Role,
    User,
)

# Combine the ModelForm (Flask-SQLAlchemy) and FlaskForm (Flask-WTF)
# See: https://wtforms-alchemy.readthedocs.io/en/latest/advanced.html#using-wtforms-alchemy-with-flask-wtf
BaseModelForm = model_form_factory(FlaskForm)


class ModelForm(BaseModelForm):
    @classmethod
    def get_session(self):
        return db.session


class MultiCheckboxField(SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """

    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class CollectionForm(FlaskForm):
    name = StringField("Nafn", validators=[InputRequired()])
    assigned_user_id = QuerySelectField("Rödd", query_factory=lambda: User.query, get_label="name", allow_blank=True)
    configuration_id = QuerySelectField(
        "Stilling",
        query_factory=lambda: Configuration.query,
        get_label="printable_name",
        allow_blank=False,
    )
    sort_by = SelectField(
        "Röðun",
        choices=[
            ("score", "Röðunarstuðull"),
            ("same", "Sömu röð og í skjali"),
            ("random", "Slembiröðun"),
        ],
    )
    is_dev = BooleanField("Tilraunarsöfnun")
    is_multi_speaker = BooleanField("Margar raddir")
    verify = BooleanField("Greina")

    def validate_assigned_user_id(self, field):
        # HACK to user the QuerySelectField on User objects
        # but then later populate the field with only the pk.
        if field.data is not None:
            field.data = field.data.id

    def validate_configuration_id(self, field):
        if field.data is not None:
            field.data = field.data.id

    def validate_is_multi_speaker(self, field):
        if field.data:
            if self.assigned_user_id.data is None:
                return True
            raise ValidationError('Ef söfnun notar margar raddir verður "Rödd" valmöguleikinn að vera tómur')
        return True


def collection_edit_form(collection):
    form = CollectionForm()
    form.assigned_user_id.default = collection.get_assigned_user()
    form.configuration_id.default = collection.configuration
    form.sort_by.default = collection.sort_by
    form.process()
    form.name.data = collection.name
    return form


class BulkTokenForm(FlaskForm):
    is_g2p = BooleanField(
        "G2P skjal.",
        description="Hakið við ef skjalið er G2P skjal samanber" + " lýsingu hér að ofan",
        default=False,
    )
    files = MultipleFileField(
        "Textaskjöl",
        description="Veljið eitt eða fleiri textaskjöl.",
        validators=[InputRequired()],
    )


class RecordForm(FlaskForm):
    token = HiddenField("Texti")
    recording = HiddenField("Upptaka")


class ExtendedRegisterForm(RegisterForm):
    """Extended the form with additional fields. The form is based on WTForms"""

    name = StringField("Nafn", [InputRequired()])
    sex = SelectField(
        "Kyn",
        [InputRequired()],
        choices=[("Kona", "Kona"), ("Karl", "Karl"), ("Annað", "Annað")],
    )
    dialect = SelectField(
        "Framburður",
        [InputRequired()],
        choices=[
            ("Linmæli", "Linmæli"),
            ("Harðmæli", "Harðmæli"),
            ("Raddaður framburður", "Raddaður framburður"),
            ("hv-framburður", "hv-framburður"),
            ("bð-, gð-framburður", "bð-, gð-framburður"),
            ("ngl-framburður", "ngl-framburður"),
            ("rn-, rl-framburður", "rn-, rl-framburður"),
            ("Vestfirskur einhljóðaframburður", "Vestfirskur einhljóðaframburður"),
            ("Skaftfellskur einhljóðaframburður", "Skaftfellskur einhljóðaframburður"),
        ],
    )
    age = IntegerField("Aldur", [InputRequired(), NumberRange(min=18, max=100)])
    is_admin = BooleanField("Notandi er vefstjóri")


class VerifierRegisterForm(RegisterForm):
    name = StringField("Nafn", [InputRequired()])


class UserEditForm(FlaskForm):
    name = StringField("Nafn")
    email = StringField("Netfang")
    dialect = SelectField(
        "Framburður",
        [InputRequired()],
        choices=[
            ("Linmæli", "Linmæli"),
            ("Harðmæli", "Harðmæli"),
            ("Raddaður framburður", "Raddaður framburður"),
            ("hv-framburður", "hv-framburður"),
            ("bð-, gð-framburður", "bð-, gð-framburður"),
            ("ngl-framburður", "ngl-framburður"),
            ("rn-, rl-framburður", "rn-, rl-framburður"),
            ("Vestfirskur einhljóðaframburður", "Vestfirskur einhljóðaframburður"),
            ("Skaftfellskur einhljóðaframburður", "Skaftfellskur einhljóðaframburður"),
        ],
    )
    sex = SelectField(
        "Kyn",
        [InputRequired()],
        choices=[("Kona", "Kona"), ("Karl", "Karl"), ("Annað", "Annað")],
    )
    age = IntegerField("Aldur")
    active = BooleanField("Virkur")


class SessionEditForm(FlaskForm):
    manager_id = QuerySelectField(
        "Stjórnandi",
        query_factory=lambda: User.query,
        get_label="name",
        validators=[InputRequired()],
    )

    def validate_manager_id(self, field):
        if field.data is not None:
            field.data = field.data.id


class DeleteVerificationForm(FlaskForm):
    verification_id = HiddenField("verification_id", validators=[InputRequired()])


class SessionVerifyForm(FlaskForm):
    """Form to verify a recording inside a session"""

    LOW = "low"
    HIGH = "high"
    WRONG = "wrong"
    GLITCH = "glitch"
    GLITCH_OUTSIDE = "glitch-outside"
    OK = "ok"
    CHOICES = [
        (LOW, "<i class='fa fa-volume-mute text-danger mr-1'></i> Of lágt (a)"),
        (HIGH, "<i class='fa fa-volume-up text-danger mr-1'></i> of hátt (s)"),
        (
            WRONG,
            "<i class='fa fa-comment-slash text-danger mr-1'></i>" + "Rangt lesið (d)",
        ),
        (GLITCH, "<i class='fa fa-times text-danger mr-1'></i> Gölluð (f)"),
        (
            GLITCH_OUTSIDE,
            "<i class='fa fa-times text-danger mr-1'></i> Galli klipptur (v)",
        ),
        (OK, "<i class='fa fa-check mr-1 text-success'></i> Góð (g)"),
    ]

    quality = MultiCheckboxField("Gæði", choices=CHOICES, validators=[InputRequired()])
    comment = StringField("Athugasemd", widget=widgets.TextArea())

    recording = HiddenField("recording", validators=[InputRequired()])
    verified_by = HiddenField("verified_by", validators=[InputRequired()])
    session = HiddenField("session", validators=[InputRequired()])
    num_verifies = HiddenField("num_verifies", validators=[InputRequired()])
    cut = HiddenField("cut", validators=[InputRequired()])
    isPriority = HiddenField("isPriority", validators=[InputRequired()])

    def validate_quality(self, field):
        data = self.quality.data
        if data is None:
            raise ValidationError("Gæði er nauðsynlegt")
        if self.LOW in data and self.HIGH in data:
            raise ValidationError("Upptakan getur ekki verið bæði of lág og of há")
        if self.OK in data and len(data) > 1:
            raise ValidationError("Upptakan getur ekki verið bæði góð og slæm")


class ConfigurationForm(FlaskForm):
    name = StringField("Nafn stillinga")
    session_sz = IntegerField(
        "Fjöldi setninga í lotu",
        [InputRequired(), NumberRange(min=1, max=100)],
        default=50,
    )
    live_transcribe = BooleanField("Nota talgreini", description="Getur haft áhrif á hljóðgæði")
    visualize_mic = BooleanField("Sýna hljóðnemaviðmót", description="Getur haft áhrif á hljóðgæði")
    analyze_sound = BooleanField("Sjálfvirk gæðastjórnun")
    auto_trim = BooleanField("Klippa hljóðbrot sjálfkrafa")
    channel_count = SelectField(
        "Fjöldi hljóðrása",
        choices=[(1, "1 rás"), (2, "2 rásir")],
        coerce=int,
        description="Athugið að hljóðrásir eru núna alltaf samþjappaðar" + " eftir upptökur.",
    )
    sample_rate = SelectField(
        "Upptökutíðni",
        choices=[
            (16000, "16,000 Hz"),
            (32000, "32,000 Hz"),
            (44100, "44,100 Hz"),
            (48000, "48,000 Hz"),
        ],
        coerce=int,
    )
    sample_size = SelectField(
        "Sýnisstærð",
        choices=[
            (16, "16 heiltölubitar"),
            (24, "24 heiltölubitar"),
            (32, "32 fleytibitar"),
        ],
        coerce=int,
        description="Ef PCM er valið sem hljóðmerkjamál er" + "sýnisstærðin 32 bitar sjálfgefið",
    )
    audio_codec = SelectField("Hljóðmerkjamál", choices=[("pcm", "PCM")])
    trim_threshold = FloatField(
        "lágmarkshljóð (dB)",
        [NumberRange(min=0)],
        default=40,
        description="Þröskuldur sem markar þögn, því lægri því meira telst "
        + "sem þögn. Þetta kemur bara af notum þegar sjálfvirk "
        + "klipping er notuð. Hljóðrófsritið er desíbel-skalað.",
    )
    too_low_threshold = FloatField(
        "Lágmarkshljóð fyrir gæði (dB)",
        [NumberRange(min=-100, max=0)],
        default=-15,
        description="Ef hljóðrófsrit upptöku fer aldrei yfir þennan "
        + "þröskuld þá mun gæðastjórnunarkerfi merkja þessa "
        + "upptöku of lága. Athugið að hér er hljóðrófsritið "
        + "skalað eftir styrk.",
    )
    too_high_threshold = FloatField(
        "Hámarkshljóð fyrir gæði (dB)",
        [NumberRange(min=-100, max=0)],
        default=-4.5,
        description="Ef hljóðrófsrit upptöku fer yfir þennan þröskuld "
        + "ákveðin fjölda af römmum í röð "
        + "þá mun gæðastjórnunarkerfi merkja þessa upptöku of "
        + "háa. Athugið að hér er hljóðrófsritið skalað eftir "
        + "styrk.",
    )
    too_high_frames = IntegerField(
        "Fjöldi of hárra ramma",
        [NumberRange(min=0, max=100)],
        default=10,
        description="Segir til um hversu margir rammar i röð þurfa að "
        + "vera fyrir ofan gæðastjórnunarþröskuldinn "
        + "til að vera merkt sem of há upptaka.",
    )
    auto_gain_control = BooleanField("Sjálfvirk hljóðstýring", description="Getur haft áhrif á hljóðgæði")
    noise_suppression = BooleanField("Dempun bakgrunnshljóðs", description="Getur haft áhrif á hljóðgæði")
    has_video = BooleanField("Myndbandssöfnun", default=False)
    video_w = IntegerField(
        "Vídd myndbands í pixlum",
        [NumberRange(min=0)],
        default=1280,
        description="Einungis notað ef söfnun er myndbandssöfnun.",
    )
    video_h = IntegerField(
        "Hæð myndbands í pixlum",
        [NumberRange(min=0)],
        default=720,
        description="Einungis notað ef söfnun er myndbandssöfnun.",
    )
    video_codec = SelectField("Myndmerkjamál", choices=[("vp8", "VP8")])


# The three form below might not be correct
# model_form function was used to create them, but is now deprecated
class RoleForm(FlaskForm):
    class Meta:
        model = Role
        exclude = ["id", "users"]


class PostingForm(FlaskForm):
    name = StringField("Nafn", [InputRequired()])
    ad_text = StringField("Texti auglýsingar", [InputRequired()], widget=widgets.TextArea())
    utterances = StringField("Setningar", [InputRequired()], widget=widgets.TextArea())

    class Meta:
        model = Posting
        exclude = ["id", "created_at", "uuid", "collection", "applications"]


class MosDetailForm(FlaskForm):
    question = StringField("Spurning", [InputRequired()])
    form_text = StringField("Form texti", [InputRequired()], widget=widgets.TextArea())
    help_text = StringField("Hjálpartexti", [InputRequired()], widget=widgets.TextArea())
    done_text = StringField("Þakkartexti", [InputRequired()], widget=widgets.TextArea())
    use_latin_square = BooleanField("Nota latin-square")
    show_text_in_test = BooleanField("Sýna texta við hljóðbút")

    class Meta:
        model = Mos
        exclude = ["id", "created_at", "uuid", "collection", "applications"]


class ApplicationForm(FlaskForm):
    name = StringField("Nafn", [InputRequired()])
    sex = SelectField(
        label="Kyn",
        validators=[InputRequired()],
        choices=[("Kona", "Kona"), ("Karl", "Karl"), ("Annað", "Annað")],
    )
    age = IntegerField("Aldur", [InputRequired(), NumberRange(min=10, max=120)])
    # voice = SelectField(
    #     label="Rödd",
    #     validators=[InputRequired()],
    #     choices=[
    #         ("sopran", "Sópran"),
    #         ("alt", "Alt"),
    #         ("tenor", "Tenór"),
    #         ("bassi", "Bassi"),
    #     ],
    # )
    email = EmailField("Netfang", [InputRequired()])
    phone = StringField("Sími")
    terms_agreement = BooleanField(
        label=Markup("Ég samþykki <a href='/tos_application/' target='_blank'>skilmála og gagnastefnu LVL</a>"),
        validators=[InputRequired()],
    )


class MosForm(ModelForm):
    class Meta:
        model = Mos
        exclude = ["uuid"]
        num_samples = IntegerField("Fjöldi setninga", [InputRequired()])

    def __init__(self, max_available, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_available = max_available

    def validate_num_samples(self, field):
        if field.data >= self.max_available or field.data < 0:
            raise ValidationError(
                "Ekki nógu markar upptökur til í safni. Sláðu inn tölu" + "á milli 0 og {}".format(self.max_available)
            )


class MosSelectAllForm(FlaskForm):
    is_synth = HiddenField()
    select = HiddenField()


class MosItemSelectionForm(ModelForm):
    class Meta:
        model = MosInstance
        exclude = ["is_synth"]


class MosTestForm(FlaskForm):
    name = StringField("Nafn", [InputRequired()])
    age = IntegerField("Aldur", [InputRequired(), NumberRange(min=10, max=120)])
    audio_setup = StringField("Hvers konar heyrnatól/hátalara ertu með?", [InputRequired()])


class UploadCollectionForm(FlaskForm):
    is_g2p = BooleanField(
        "Staðlað form.",
        description="Hakið við ef uphleðslan er á stöðluðu" + " formi samanber lýsingu hér að ofan",
        default=False,
    )
    is_lobe_collection = BooleanField(
        "LOBE söfnun.",
        description="Hakið við ef uphleðslan er LOBE söfnun" + " á sama formi og LOBE söfnun er hlaðið niður",
        default=False,
    )
    name = StringField("Nafn", validators=[InputRequired()])
    assigned_user_id = QuerySelectField("Rödd", query_factory=lambda: User.query, get_label="name", allow_blank=True)
    configuration_id = QuerySelectField(
        "Stilling",
        query_factory=lambda: Configuration.query,
        get_label="printable_name",
        allow_blank=False,
    )
    sort_by = SelectField(
        "Röðun",
        choices=[
            ("score", "Röðunarstuðull"),
            ("same", "Sömu röð og í skjali"),
            ("random", "Slembiröðun"),
        ],
    )
    is_dev = BooleanField("Tilraunarsöfnun")
    is_multi_speaker = BooleanField("Margar raddir")

    files = FileField(
        validators=[
            FileAllowed(["zip"], "Skrá verður að vera zip mappa"),
            FileRequired("Hladdu upp zip skrá"),
        ]
    )

    def validate_assigned_user_id(self, field):
        # HACK to user the QuerySelectField on User objects
        # but then later populate the field with only the pk.
        if field.data is not None:
            field.data = field.data.id

    def validate_configuration_id(self, field):
        if field.data is not None:
            field.data = field.data.id

    def validate_is_g2p(self, field):
        if field.data:
            if not self.is_lobe_collection.data:
                return True
            else:
                raise ValidationError("Velja verður annað hvort staðlað form" + " Eða LOBE söfnun")
        else:
            if self.is_lobe_collection.data:
                return True
            else:
                raise ValidationError("Velja verður annað hvort staðlað form" + " Eða LOBE söfnun")

    def validate_is_lobe_collection(self, field):
        if field.data:
            if not self.is_g2p.data:
                return True
            else:
                raise ValidationError("Velja verður annað hvort staðlað form" + "eða LOBE söfnun")
        else:
            if self.is_g2p.data:
                return True
            else:
                raise ValidationError("Velja verður annað hvort staðlað form" + "eða LOBE söfnun")


class MosUploadForm(FlaskForm):
    is_g2p = BooleanField(
        "Staðlað form.",
        description="Hakið við ef skráin er á stöðluðu formi" + " samanber lýsingu hér að ofan",
        default=False,
    )
    files = FileField(
        validators=[
            FileAllowed(["zip"], "Skrá verður að vera zip mappa"),
            FileRequired("Hladdu upp zip skrá"),
        ]
    )


class PostLinkForm(FlaskForm):
    link = StringField("Youtube hlekkur:", [InputRequired()])
    link = StringField("Youtube hlekkur:", [InputRequired()])

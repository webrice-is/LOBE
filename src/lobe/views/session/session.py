import traceback

from flask import Blueprint
from flask import current_app as app
from flask import flash, redirect, render_template, request, url_for
from flask_security import current_user, login_required, roles_accepted

from lobe.database_functions import delete_session_db, resolve_order
from lobe.forms import SessionEditForm
from lobe.models import PrioritySession, Recording, Session, db

session = Blueprint("session", __name__, template_folder="templates")


@session.route("/sessions/")
@login_required
@roles_accepted("admin", "Notandi")
def rec_session_list():
    page = int(request.args.get("page", 1))
    sessions = Session.query.order_by(
        resolve_order(
            Session,
            request.args.get("sort_by", default="created_at"),
            order=request.args.get("order", default="desc"),
        )
    ).paginate(page=page, per_page=app.config["SESSION_PAGINATION"])
    isPriority = False
    return render_template(
        "session_list.jinja",
        sessions=sessions,
        isPriority=isPriority,
        section="session",
    )


@session.route("/prioritySessions/")
@login_required
@roles_accepted("admin", "Notandi")
def priority_session_list():
    page = int(request.args.get("page", 1))
    sessions = PrioritySession.query.order_by(
        resolve_order(
            PrioritySession,
            request.args.get("sort_by", default="created_at"),
            order=request.args.get("order", default="desc"),
        )
    ).paginate(page=page, per_page=app.config["SESSION_PAGINATION"])
    isPriority = True
    return render_template(
        "session_list.jinja",
        sessions=sessions,
        isPriority=isPriority,
        section="session",
    )


@session.route("/sessions/<int:id>/")
@login_required
@roles_accepted("admin", "Notandi")
def rec_session_detail(id):
    session = Session.query.get(id)
    return render_template("session.jinja", session=session, section="session")


@session.route("/sessions/<int:id>/mark/priority")
@login_required
@roles_accepted("admin")
def mark_session_as_priority(id):
    session = Session.query.get(id)
    session.has_priority = True
    db.session.commit()
    return render_template("session.jinja", session=session, section="session")


@session.route("/sessions/<int:id>/unmark/priority")
@login_required
@roles_accepted("admin")
def unmark_session_as_priority(id):
    session = Session.query.get(id)
    session.has_priority = False
    db.session.commit()
    return render_template("session.jinja", session=session, section="session")


@session.route("/priority/sessions/<int:id>/")
@login_required
@roles_accepted("admin", "Notandi")
def rec_priority_session_detail(id):
    session = PrioritySession.query.get(id)
    return render_template("session.jinja", session=session, section="session")


@session.route("/sessions/addpriority/<int:session_id>/<int:recording_id>/")
@login_required
@roles_accepted("admin")
def add_recording_to_priority_session(session_id, recording_id):
    session = PrioritySession.query.get(session_id)
    recording = Recording.query.get(recording_id)
    recording.priority_session_id = session_id
    session.is_verified = False
    db.session.commit()
    return redirect(url_for("recording.recording_detail", id=recording_id))


@session.route("/sessions/create_priority_session/<int:recording_id>/")
@login_required
@roles_accepted("admin")
def create_priority_session(recording_id):
    recording = Recording.query.get(recording_id)
    session = PrioritySession(
        current_user.id,
        None,
        current_user.id,
        duration=None,
        has_video=False,
        is_dev=False,
    )
    db.session.add(session)
    db.session.flush()
    session_id = session.id
    recording.priority_session_id = session_id
    db.session.commit()
    if session:
        print(session.id)
        flash(
            "Forgangslota {} var búin til og upptaka sett í hana".format(session.get_printable_id()),
            category="success",
        )
    return redirect(url_for("recording.recording_detail", id=recording_id))


@session.route("/sessions/<int:id>/edit/", methods=["GET", "POST"])
@login_required
@roles_accepted("admin")
def session_edit(id):
    session = Session.query.get(id)
    form = SessionEditForm(request.form)
    try:
        if request.method == "POST" and form.validate():
            form.populate_obj(session)
            db.session.commit()
            flash("Lotu var breytt", category="success")
    except Exception as error:
        app.logger.error("Error updating a session : {}\n{}".format(error, traceback.format_exc()))
    return render_template(
        "forms/model.jinja",
        form=form,
        type="edit",
        action=url_for("session.session_edit", id=id),
        section="session",
    )


@session.route("/sessions/<int:id>/delete/", methods=["GET"])
@login_required
@roles_accepted("admin")
def delete_session(id):
    record_session = Session.query.get(id)
    did_delete = delete_session_db(record_session)
    if did_delete:
        flash("Lotu var eytt", category="success")
    else:
        flash("Ekki gekk að eyða lotu", category="warning")
    return redirect(url_for("session.rec_session_list"))

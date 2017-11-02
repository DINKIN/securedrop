# -*- coding: utf-8 -*-

from flask import (request, send_file, redirect, flash,
                   url_for, abort)
from sqlalchemy.orm.exc import NoResultFound

import config
from flask_babel import gettext
import store
from db import db_session, Submission

from journalist_app import create_app
from journalist_app.decorators import login_required
from journalist_app.utils import (col_star,
                                  col_un_star,
                                  col_delete,
                                  col_download_unread,
                                  col_download_all)

app = create_app(config)


@app.route('/col/process', methods=('POST',))
@login_required
def col_process():
    actions = {'download-unread': col_download_unread,
               'download-all': col_download_all, 'star': col_star,
               'un-star': col_un_star, 'delete': col_delete}
    if 'cols_selected' not in request.form:
        flash(gettext('No collections selected.'), 'error')
        return redirect(url_for('main.index'))

    # getlist is cgi.FieldStorage.getlist
    cols_selected = request.form.getlist('cols_selected')
    action = request.form['action']

    if action not in actions:
        return abort(500)

    method = actions[action]
    return method(cols_selected)


@app.route('/col/<filesystem_id>/<fn>')
@login_required
def download_single_submission(filesystem_id, fn):
    """Sends a client the contents of a single submission."""
    if '..' in fn or fn.startswith('/'):
        abort(404)

    try:
        Submission.query.filter(
            Submission.filename == fn).one().downloaded = True
        db_session.commit()
    except NoResultFound as e:
        app.logger.error("Could not mark " + fn + " as downloaded: %s" % (e,))

    return send_file(store.path(filesystem_id, fn),
                     mimetype="application/pgp-encrypted")


if __name__ == "__main__":  # pragma: no cover
    debug = getattr(config, 'env', 'prod') != 'prod'
    app.run(debug=debug, host='0.0.0.0', port=8081)

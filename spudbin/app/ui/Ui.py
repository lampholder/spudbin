"""All the UI gubbins"""
from flask import render_template

from spudbin.app import app

@app.route('/potatoes', methods=['GET'])
def ui_submit_tokens():
    """UI for submitting tokens"""
    return render_template('hello_world.html', my_string='xyzzy')


#def is_authed(username):
#    if 'github_token' not in session:
#        return False
#    with Database.connection() as connection:
#        users = USERS.fetch_by_username(username, connection)
#    if users is None:
#        return False #XXX: Gotta do better than this
#    auth_test = requests.get('https://api.github.com/user',
#                             params={'access_token': session['github_token']})
#    return auth_test.status_code != 200
#
#def bauthenticate(username):
#    if not is_authed(username):
#        return redirect('https://spudb.in/login', code='302')
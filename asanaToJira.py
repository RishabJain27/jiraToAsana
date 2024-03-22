from __main__ import app

@app.route('/asanaWebHook', methods=['GET'])
def asanaWebHook():
    return 'it works!'

def message(backend, user, response, *args, **kwargs):
    if backend.name == 'twitter':
        print"\nAR 15 Rachel Maddow %s \n"%user.profile.firstName


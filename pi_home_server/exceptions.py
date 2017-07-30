
class UserOrPasswordNotProvidedException(Exception):
    message = 'username or password not provided'


class UserOrPasswordInvalidException(Exception):
    message = 'username or password not valid'


class SaveUserException(Exception):
    message = 'uknown error while saving the user'

class NotSquareImageException(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return 'Image is not square'

__all__ = [
    'ValidationError',
    'JSONLineDecodeError',
]


class ValidationError(ValueError):
    """Exception that is raised by an error encountered in validating an input parameter or content.
    This is a generic error raised for errors encountered when functions like
    `load_dataset` when loading contents of a file.

    See Also
    --------
    load_dataset : Loads dataset into a DataFrame.
    read_html : Read HTML table into a DataFrame.
    """


class JSONLineDecodeError(Exception):
    """JSON line decode error.

    Raise when there is an error in reading a JSON line file. Analogous to  `json.JSONDecodeError`.

    See Also
    --------
    jsonline.load : Loads jsonline file into a dict.
    """

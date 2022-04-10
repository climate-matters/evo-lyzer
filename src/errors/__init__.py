__all__ = [
    'ValidationError',
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

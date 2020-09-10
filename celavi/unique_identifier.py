class UniqueIdentifier:
    _unique_identifier_integer = 0

    @classmethod
    def unique_identifier(cls) -> int:
        """
        This returns a UUID that can serve as a unique identifier for anything.
        These UUIDs can be used as keys in a set or hash if needed.

        TODO: Replace this with an incrementing integer.

        Returns
        -------
        str
            A UUID to be used as a unique identifier.
        """
        cls._unique_identifier_integer += 1
        return cls._unique_identifier_integer
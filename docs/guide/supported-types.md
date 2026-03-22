# Supported Types

Pydantic Wizard supports interactive prompting for the following types:

## Scalar Types

- `str`
- `int`
- `float`
- `bool`
- `Decimal`

## Enum and Literal

- `enum.Enum` subclasses
- `typing.Literal`

## Date and Time

- `datetime`
- `time`
- `timedelta`

## Composite Types

- `Optional[T]`
- `List[T]`
- `Set[T]`
- `Dict[K, V]`
- `Union[T1, T2, ...]`
- Nested `BaseModel` subclasses

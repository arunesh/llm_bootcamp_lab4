# Custom override decorator
def override(method):
    def wrapper(cls_method):
        # Ensure the method exists in the base class
        if not hasattr(method.__self__.__class__, method.__name__):
            raise TypeError(f"Method '{method.__name__}' is not overriding any method from the parent class.")
        return cls_method
    return wrapper
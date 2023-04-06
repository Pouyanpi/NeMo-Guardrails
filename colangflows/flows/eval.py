import re

from simpleeval import simple_eval

from colangflows.flows.utils import AttributeDict


def eval_expression(expr, context):
    """Evaluates the provided expression in the given context."""
    # If it's not a string, we should return it as such
    if expr is None:
        return None

    if not isinstance(expr, str):
        assert isinstance(expr, bool) or isinstance(expr, int)

        return expr

    # We search for all variable names starting with $, remove the $ and add
    # the value in the globals dict for eval
    var_names = re.findall(r"\$([a-zA-Z_][a-zA-Z0-9_]*)", expr)
    updated_expr = re.sub(r"\$([a-zA-Z_][a-zA-Z0-9_]*)", r"var_\1", expr)
    expr_locals = {}

    for var_name in var_names:
        # if we've already computed the value, we skip
        if f"var_{var_name}" in expr_locals:
            continue

        val = context.get(var_name)

        # We transform dicts to AttributeDict so we can access their keys as attributes
        # e.g. write things like $speaker.name
        if isinstance(val, dict):
            val = AttributeDict(val)

        expr_locals[f"var_{var_name}"] = val

    # Finally, just evaluate the expression
    try:
        # TODO: replace this with something even more restrictive.
        return simple_eval(updated_expr, names=expr_locals)
    except Exception as ex:
        raise Exception(f"Error evaluating '{expr}': {str(ex)}")

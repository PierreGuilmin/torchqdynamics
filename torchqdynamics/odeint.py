import warnings

import torch

# --------------------------------------------------------------------------------------
#     Main odeint function
# --------------------------------------------------------------------------------------


def odeint(qsolver, y0, tsave, sensitivity='autograd', model_params=None):
    # Check arguments
    tsave = check_tsave(tsave)
    if (model_params is not None) and (sensitivity in [None, 'autograd']):
        warnings.warn('Argument `model_params` was supplied in `odeint` but not used.')

    # Dispatch to appropriate odeint subroutine
    if sensitivity is None:
        return odeint_inplace(qsolver, y0, tsave)
    elif sensitivity == 'autograd':
        return odeint_main(qsolver, y0, tsave)
    elif sensitivity == 'adjoint':
        return odeint_adjoint(qsolver, y0, tsave, model_params)


# --------------------------------------------------------------------------------------
#     Core subroutines
# --------------------------------------------------------------------------------------


def odeint_main(qsolver, y0, tsave):
    if qsolver.options.stepclass == 'fixed':
        return _fixed_odeint(qsolver, y0, tsave)
    elif qsolver.options.stepclass == 'adaptive':
        return _adaptive_odeint(qsolver, y0, tsave)


def odeint_inplace(qsolver, y0, tsave):
    raise NotImplementedError


def odeint_adjoint(qsolver, y0, tsave, model_params):
    raise NotImplementedError


def _adaptive_odeint(qsolver, y0, tsave):
    raise NotImplementedError


def _fixed_odeint(qsolver, y0, tsave):
    # Initialize save tensor
    ysave = torch.zeros((len(tsave), ) + y0.shape).to(y0)
    save_counter, save_flag = 0, False
    if tsave[0] == 0:
        ysave[0] = y0
        save_counter += 1

    # Get qsolver fixed time step
    dt = qsolver.options.dt

    # Run the ODE routine
    t, y = 0, y0
    while t < tsave[-1]:
        # Check if final time is reached
        if t + dt > tsave[-1]:
            dt = tsave[-1] - t

        # Iterate solution
        y = qsolver.forward(t, dt, y)
        t = t + dt

        # Save solution
        if t >= tsave[save_counter]:
            ysave[save_counter] = y
            save_counter += 1

    return tsave, ysave


# --------------------------------------------------------------------------------------
#     Utility functions
# --------------------------------------------------------------------------------------


def check_tsave(tsave):
    """Check tsave is a sorted 1-D torch.tensor"""
    if isinstance(tsave, (list, np.ndarray)):
        tsave = torch.cat(tsave)
    if tsave.dim != 1 or len(tsave) == 0:
        raise ValueError('Argument `tsave` should be a non-empty 1-D torch.Tensor.')
    if not torch.all(torch.diff(tsave) > 0):
        raise ValueError(
            'Argument `tsave` is not sorted in ascending order '
            'or contains duplicate values.'
        )
    return tsave
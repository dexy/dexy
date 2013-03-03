from dexy.commands.utils import init_wrapper
from dexy.commands.utils import D

def reset_command(
        __cli_options=False,
        artifactsdir=D['artifacts_dir'], # location of directory in which to store artifacts
        logdir=D['log_dir']# location of directory in which to store logs
        ):
    """
    Empty the artifacts and logs directories.
    """
    wrapper = init_wrapper(locals())
    wrapper.remove_dexy_dirs()
    wrapper.setup_dexy_dirs()

def cleanup_command(
        __cli_options=False,
        artifactsdir=D['artifacts_dir'], # location of directory in which to store artifacts
        logdir=D['log_dir'], # location of directory in which to store logs
        reports=True # Also remove report generated dirs
        ):
    """
    Remove the artifacts and logs directories.
    """
    wrapper = init_wrapper(locals())
    wrapper.remove_dexy_dirs(reports)

def setup_command(__cli_options=False, **kwargs):
    """
    Create the directories dexy needs to run. This helps make sure you mean to run dexy in this directory.
    """
    wrapper = init_wrapper(locals())
    wrapper.setup_dexy_dirs()


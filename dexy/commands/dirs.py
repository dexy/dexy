from dexy.commands.utils import init_wrapper
from dexy.utils import defaults

def reset_command(
        __cli_options=False,
        artifactsdir=defaults['artifacts_dir'], # location of directory in which to store artifacts
        logdir=defaults['log_dir']# location of directory in which to store logs
        ):
    """
    Empty the artifacts and logs directories.
    """
    wrapper = init_wrapper(locals())
    wrapper.remove_dexy_dirs()
    wrapper.remove_reports_dirs(keep_empty_dir=True)
    wrapper.create_dexy_dirs()

def cleanup_command(
        __cli_options=False,
        artifactsdir=defaults['artifacts_dir'], # location of directory in which to store artifacts
        logdir=defaults['log_dir'], # location of directory in which to store logs
        reports=True # Also remove report generated dirs
        ):
    """
    Remove the artifacts and logs directories.
    """
    wrapper = init_wrapper(locals())
    wrapper.remove_dexy_dirs()
    wrapper.remove_reports_dirs(reports)

def setup_command(__cli_options=False, **kwargs):
    """
    Create the directories dexy needs to run. This helps make sure you mean to run dexy in this directory.
    """
    wrapper = init_wrapper(locals())
    wrapper.create_dexy_dirs()


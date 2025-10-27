from collective.documentgenerator import utils as dg_utils

old_clean_notes = dg_utils.clean_notes


def clean_notes(pod_template):
    """Speed up tests by not cleaning notes."""
    pass


dg_utils.clean_notes = clean_notes

from distutils.dep_util import newer_group


# yes, this is was almost entirely copy-pasted from
# 'newer_pairwise()', this is just another convenience
# function.
def newer_pairwise_group(sources_groups, targets):
    """Walk both arguments in parallel, testing if each source group is newer
    than its corresponding target. Returns a pair of lists (sources_groups,
    targets) where sources is newer than target, according to the semantics
    of 'newer_group()'.
    """
    if len(sources_groups) != len(targets):
        raise ValueError(
            "'sources_group' and 'targets' must be the same length")

    # build a pair of lists (sources_groups, targets) where source is newer
    n_sources = []
    n_targets = []
    for i in range(len(sources_groups)):
        if newer_group(sources_groups[i], targets[i]):
            n_sources.append(sources_groups[i])
            n_targets.append(targets[i])

    return n_sources, n_targets

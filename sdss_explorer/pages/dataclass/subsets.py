"""Subsets and SubsetState dataclasses, including all relevant add/remove/rename/clone callbacks."""

import dataclasses
import solara as sl

from .alert import Alert


# frozen means it yells at us if we do assignment instead of replace
@dataclasses.dataclass(frozen=True)
class Subset:
    """Subset dataclass."""
    name: str = 'A'
    expression: str = ''
    dataset: str = 'aspcap'  # TODO: change to astra best when Andy makes it
    flags: list[str] = dataclasses.field(
        default_factory=lambda: ['Purely non-flagged'])
    mapper: list[str] = dataclasses.field(default_factory=list)
    carton: list[str] = dataclasses.field(default_factory=list)


class SubsetState:
    """Subset storage namespace, with functions for add/remove/etc."""
    index = sl.reactive(1)
    subsets = sl.reactive({'s0': Subset()})

    @staticmethod
    def add_subset(name: str, **kwargs) -> bool:
        """Adds subset and subsetcard, generating new unique key for subset. Boolean return for success."""
        for subset in SubsetState.subsets.value.values():
            if name == subset.name:
                Alert.update("Subset with name already exists!", color="error")
                return False
        if len(name) == 0:
            Alert.update("Please enter a name for the subset.",
                         color="warning")
            return False

        else:  # no name case
            # add subset
            key = SubsetState.index.value
            subsets = SubsetState.subsets.value.copy()
            subsets.update({'s' + str(key): Subset(name=name, **kwargs)})
            SubsetState.subsets.set(dict(**subsets))

            # iterate index
            SubsetState.index.set(SubsetState.index.value + 1)
            return True

    @staticmethod
    def update_subset(key: str, **kwargs) -> bool:
        """Updates subset of key with specified kwargs"""
        if key not in SubsetState.subsets.value.keys():
            Alert.update(
                f"BUG: subset update failed! Key {key} not in hashmap.",
                color="error")
            return False

        subsets = SubsetState.subsets.value.copy()
        subset = SubsetState.subsets.value[key]
        subsets[key] = dataclasses.replace(subset, **kwargs)
        SubsetState.subsets.set(dict(**subsets))
        return True

    @staticmethod
    def rename_subset(key: str, newname: str) -> bool:
        """Rename subset method, with specific logic"""
        if key not in SubsetState.subsets.value.keys():
            Alert.update("BUG: subset clone failed! Key not in hashmap.",
                         color="error")
            return False
        elif len(newname) == 0:
            Alert.update("Enter a name for the subset!", color='warning')
            return False
        elif newname == SubsetState.subsets.value[key].name:
            Alert.update("Name is the same!", color='warning')
            return False
        elif newname in [ss.name for ss in SubsetState.subsets.value.values()]:
            Alert.update("Name already exists!", color='warning')
            return False
        else:
            return SubsetState.update_subset(key, name=newname)

    @staticmethod
    def clone_subset(key: str) -> bool:
        """Clones a subset"""
        if key not in SubsetState.subsets.value.keys():
            Alert.update("BUG: subset clone failed! Key not in hashmap.",
                         color="error")
            return False
        else:
            subsets = SubsetState.subsets.value.copy()
            subset = SubsetState.subsets.value[key]
            # TODO: name logic
            name = 'copy of ' + subset.name
            newkey = 's' + str(SubsetState.index.value)
            SubsetState.index.set(SubsetState.index.value + 1)

            subsets.update({newkey: dataclasses.replace(subset, name=name)})
            SubsetState.subsets.set(dict(**subsets))

    @staticmethod
    def remove_subset(key: str):
        """
        Removes a subset from the Subset master list.

        :key: string key of subset
        """
        # dict comprehension for reconstruction
        SubsetState.subsets.value = dict(**{
            k: v
            for k, v in SubsetState.subsets.value.items() if k != key
        })

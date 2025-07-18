"""Subsets and SubsetState dataclasses, including all relevant add/remove/rename/clone callbacks."""

import dataclasses
import solara as sl
import vaex as vx

from .alert import Alert
from .state import State
import logging

logger = logging.getLogger("dashboard")


# frozen means it yells at us if we do assignment instead of replace
@dataclasses.dataclass(frozen=True)
class Subset:
    """Subset dataclass.

    Attributes:
        name: subset name
        expresssion: custom filter expression
        dataset: specific dataset
        flags: toggled quick flags list
        carton: selected targeting cartons
        mapper: selected mapper programs
        crossmatch: multi-line string of crossmatch identifiers
        cmtype: type of crossmatch
        df: vaex dataframe, corresponds to dataset
        columns: specific columns, used internally to guardrail users and reset valid columns

    """

    name: str = "A"
    expression: str = ""
    dataset: str = dataclasses.field(default_factory=State.get_default_dataset)
    flags: list[str] = dataclasses.field(
        default_factory=lambda: ["purely non-flagged"])
    carton: list[str] = dataclasses.field(default_factory=list)
    mapper: list[str] = dataclasses.field(default_factory=list)
    crossmatch: str = ""
    cmtype: str = "gaia_dr3"
    df: vx.DataFrame = dataclasses.field(default_factory=State.get_df)
    columns: list[str] = dataclasses.field(default_factory=list)

    def __repr__(self) -> str:
        return "\n".join(
            f"{k:15}: {v}" for k, v in {
                "name": self.name,
                "id": State.uuid,
                "df": hex(id(self.df)),
                "expression": self.expression,
                "dataset": self.dataset,
                "carton": self.carton,
                "mapper": self.mapper,
            }.items())


class SubsetData:
    """User-facing subset reactive class, with functions for add/remove/etc.

    Attributes:
        index (solara.Reactive[int]): index, used to ensure unique keys
        subsets (solara.Reactive[dict[str,Subset]]): dictionary of keys to subsets

    """

    def __init__(self):
        self.index = sl.reactive(1)
        self.subsets = sl.reactive({"s0": Subset()})

    def add_subset(self, name: str, **kwargs) -> bool:
        """Adds subset and subsetcard, generating new unique key for subset.

        Args:
            key: subset key
            kwargs (kwargs): keyword arguments to instantiate `Subset` with

        Returns:
            bool: `True` if successful, `False` if not.
        """
        for subset in self.subsets.value.values():
            if name == subset.name:
                Alert.update("Subset with name already exists!", color="error")
                return False
        if len(name) == 0:
            Alert.update("Please enter a name for the subset.",
                         color="warning")
            return False

        else:  # no name case
            # add subset
            key = self.index.value
            subsets = self.subsets.value.copy()
            subsets.update({"s" + str(key): Subset(name=name, **kwargs)})
            self.subsets.set(dict(**subsets))
            logger.debug("Adding subset with key s" + str(key))
            logger.debug(str(self.subsets.value["s" + str(key)]))

            # iterate index
            self.index.set(self.index.value + 1)
            return True

    def update_subset(self, key: str, **kwargs) -> bool:
        """Updates subset of key with specified kwargs

        Args:
            key: subset key
            kwargs (kwargs): keyword arguments to update with

        Returns:
            bool: `True` if successful, `False` if not.
        """
        if key not in self.subsets.value.keys():
            Alert.update(
                f"BUG: subset update failed! Key {key} not in hashmap.",
                color="error")
            return False

        subsets = self.subsets.value.copy()
        subset = self.subsets.value[key]
        subsets[key] = dataclasses.replace(subset, **kwargs)
        self.subsets.set(dict(**subsets))
        return True

    def rename_subset(self, key: str, newname: str) -> bool:
        """Renames a subset.

        Args:
            key: subset key
            newname: new name for subset

        Returns:
            bool: `True` if successful, `False` if not.
        """
        if key not in self.subsets.value.keys():
            Alert.update("BUG: subset clone failed! Key not in hashmap.",
                         color="error")
            return False
        elif len(newname) == 0:
            Alert.update("Enter a name for the subset!", color="warning")
            return False
        elif newname == self.subsets.value[key].name:
            Alert.update("Name is the same!", color="warning")
            return False
        elif newname in [ss.name for ss in self.subsets.value.values()]:
            Alert.update("Name already exists!", color="warning")
            return False
        else:
            return self.update_subset(key, name=newname)

    def clone_subset(self, key: str) -> bool:
        """Clones a subset.

        Args:
            key: subset key

        Returns:
            bool: `True` if successful, `False` if not.
        """
        if key not in self.subsets.value.keys():
            Alert.update("BUG: subset clone failed! Key not in hashmap.",
                         color="error")
            return False
        else:
            subsets = self.subsets.value.copy()
            subset = self.subsets.value[key]
            # TODO: better name logic
            name = "copy of " + subset.name
            newkey = "s" + str(self.index.value)
            self.index.set(self.index.value + 1)

            subsets.update({newkey: dataclasses.replace(subset, name=name)})
            self.subsets.set(dict(**subsets))
            return True

    def remove_subset(self, key: str):
        """
        Removes a subset from the Subset master list.

        Args:
            key: subset key
        """
        # dict comprehension for reconstruction
        self.subsets.value = dict(**{
            k: v
            for k, v in self.subsets.value.items() if k != key
        })


SubsetState = SubsetData()
"""Specific SubsetData instance used for app."""

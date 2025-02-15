<template>
  <v-autocomplete
    v-model="value"
    :label="label"
    :items="values"
    :small-chips="multiple"
    :multiple="multiple"
    :deletable-chips="multiple"
    :auto-select-first="multiple"
    chips
    validate-on-blur
    hide-selected
    style="width: 100%"
    filled
    return-object
    :search-input.sync="searchInput"
    @change="searchInput=''"
  />
</template>
<script>
  export default {
  data () {
      return {
        searchInput: null,
      }
    },
      methods: {
            customFilter (item, queryText, itemText) {
              const textOne = item.name.toLowerCase()
              const textTwo = item.abbr.toLowerCase()
              const searchText = queryText.toLowerCase()

              return textOne.indexOf(searchText) > -1 ||
                textTwo.indexOf(searchText) > -1
            },
    },
  }
</script>

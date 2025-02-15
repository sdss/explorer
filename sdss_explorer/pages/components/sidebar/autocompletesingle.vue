<template>
  <v-autocomplete
    v-model="displayValue"
    :label="label"
    :items="values"
    :disabled="disabled"
    validate-on-blur
    hide-selected
    style="width: 100%"
    filled
    @blur="handleBlur"
    @change="handleInput"
    return-object
  />
</template>
<script>
  export default {
  data () {
      return {
        value: '',
        displayValue: '',
        label: 'Temp label, if you see this something went wrong',
        values: ['foo', 'bar'],
        disabled: false,
        allow_none: false
      }
    },
  created() {
  this.displayValue = this.value
  },
    watch: {
      value(val) {
        console.log("value is", val)
      }
    },
 methods: {
    handleInput(newValue) {
      console.log('Current',this.value);
      console.log('New',newValue);
      if (!this.allow_none && (!newValue || newValue === '' )) {
        // Just keep the current value by doing nothing, it will be sanitized on blur
        return
      }
      this.value = newValue
      this.displayValue = newValue
        },
      handleBlur() {
      if (!this.allow_none && (!this.displayValue || this.displayValue === '')) {
        console.log('Reset on blur');
        this.displayValue = this.value;
      }
      }}}
</script>

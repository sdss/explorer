<template>
  <v-text-field
    v-model="model"
    :error="error"
    :messages="messages"
    label="Enter an expression"
    placeholder="teff < 15e3 & (mg_h > -1 | fe_h < -2)"
    clearable
    validate-on-blur
    outlined 
    @keyup.enter="onEnter"
    @blur="onEnter"
  >
    <template v-slot:append-outer>
      <v-tooltip bottom>
        <template v-slot:activator="{ on }">
          <v-icon 
            v-on="on"
            @mouseenter="hovered = true"
            @mouseleave="hovered = false"
            :class="hovered ? 'hovered' : ''"
            @click="on_append"
          >
            mdi-information-outline
          </v-icon>
        </template>
        <span>Help</span>
      </v-tooltip>
    </template>
  </v-text-field>
</template>
<script>
export default {
 data() {
    return {
      value: "",
      model: "",
      messages: [],
      error: false,
      hovered: false, // hover state
    }
  },
  created() {
    // copy the value to model when component is created; for query param init
    this.model = this.value;
  },
  methods: {
      onEnter(event) {
      // this.$emit('enter', event);
      // optional: trigger blur on enter
      //event.target.blur();
      this.value = this.model;
    }
  }
}
</script>
<style>
.v-icon.hovered {
  color: #2196F3 !important;
}
.v-icon {
  transition: color 0.3s ease;
}
</style>

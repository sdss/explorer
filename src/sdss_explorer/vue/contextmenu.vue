<template>
  <v-menu v-model="menu" :absolute="abso" offset-y :position-x=event.pageX :position-y=event.pageY>
    <template v-slot:activator="activator">
    </template>
    <v-list v-for="index in 4" :key="index" style="padding: 0;">
      <v-list-item-title>Item "key"</v-list-item-title>
    </v-list>
  </v-menu>
</template>

<script>
module.exports = {
  methods: {
    show(e, on) {
      // hide menu, and trigger the event on the next tick, otherwise vue does not see
      // `show_menu` changing and will no do any animation
      this.menu = false;
      this.$nextTick(() => {
        on.click(e)
      })
    }
  }
}
</script>

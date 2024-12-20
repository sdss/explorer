<template>
    <div v-if="!loaded">Loading bokeh...</div>
</template>
<script>
module.exports = {
    mounted() {
        const check = () => {
            if (window.Bokeh) {
                this.loaded = true;
                return;
            }
            setTimeout(check, 100);
        }
        check();
    }
}
</script>

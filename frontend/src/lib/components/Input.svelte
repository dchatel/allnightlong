<script lang="ts">
    let {
        value,
        id = null,
        isEditing = false,
        class: className = '',
        onchange,
    } = $props();
</script>

{#if isEditing}
    <input
        {id}
        type="text"
        class={className}
        {value}
        oninput={(e) => onchange?.(e.currentTarget.value)}
    />
{:else}
    <span {id} class={className}>{value}</span>
{/if}
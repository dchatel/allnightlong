<script lang="ts">
  import { getCurrentWindow } from '@tauri-apps/api/window';
  const appWindow = getCurrentWindow();

  let { isMaximized } = $props();

  const minimize = () => appWindow.minimize();
  const toggleMaximize = () => appWindow.toggleMaximize();
  const close = () => appWindow.close();
</script>

<!-- L'attribut data-tauri-drag-region permet de déplacer la fenêtre en glissant cette div -->
<div data-tauri-drag-region class="titlebar">
  <div class="logo">🔭 AwakeTonight</div>
  
  <div class="window-controls">
    <button class="control-btn" onclick={minimize} title="Réduire">
      <svg width="16" height="16" viewBox="0 0 24 24"><path fill="white" d="M20 14H4v-4h16"/></svg>
    </button>
    
    <button class="control-btn" onclick={toggleMaximize} title={isMaximized ? "Restaurer" : "Agrandir"}>
      {#if isMaximized}
        <svg width="16" height="16" viewBox="0 0 24 24"><path fill="white" d="M4 8h4V4h12v12h-4v4H4V8zm12 0V6H10v2h6zm-8 4v6h6v-6H8z"/></svg>
      {:else}
        <svg width="16" height="16" viewBox="0 0 24 24"><path fill="white" d="M4 4h16v16H4V4zm2 4v10h12V8H6z"/></svg>
      {/if}
    </button>

    <button class="control-btn close" onclick={close} title="Fermer">
      <svg width="16" height="16" viewBox="0 0 24 24"><path fill="white" d="M19 6.41L17.59 5L12 10.59L6.41 5L5 6.41L10.59 12L5 17.59L6.41 19L12 13.41L17.59 19L19 17.59L13.41 12z"/></svg>
    </button>
  </div>
</div>

<style>
  .titlebar {
    height: 40px;
    background: #1a1a1d;
    display: flex;
    justify-content: space-between;
    align-items: center;
    user-select: none; /* Empêche de sélectionner le texte de la barre */
    border-bottom: 1px solid #333;
  }

  .logo {
    padding-left: 15px;
    font-size: 0.9rem;
    font-weight: bold;
    color: #aaa;
    pointer-events: none; /* Laisse le clic passer à la zone de drag en dessous */
  }

  .window-controls {
    display: flex;
    height: 100%;
  }

  .control-btn {
    display: inline-flex;
    justify-content: center;
    align-items: center;
    width: 45px;
    height: 100%;
    border: none;
    background: transparent;
    cursor: pointer;
    transition: background 0.2s;
  }

  .control-btn:hover {
    background: #333;
  }

  .control-btn.close:hover {
    background: #e81123; /* Rouge classique Windows au survol */
  }
</style>
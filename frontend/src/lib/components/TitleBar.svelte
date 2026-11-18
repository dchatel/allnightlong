<script lang="ts">
  import { getCurrentWindow } from '@tauri-apps/api/window';
  import { appState } from '$lib/state.svelte';

  const appWindow = getCurrentWindow();

  let { isMaximized } = $props();

  const minimize = () => appWindow.minimize();
  const toggleMaximize = () => appWindow.toggleMaximize();
  const close = () => appState.closeApp();
</script>

<!-- L'attribut data-tauri-drag-region permet de déplacer la fenêtre en glissant cette div -->
<div data-tauri-drag-region class="titlebar">
  <div class="logo">🔭 AwakeTonight</div>
  
  <div class="window-controls">
    <button class="control-btn" onclick={() => (appState.showLocations = true)} title="Lieux d'observation">
      <svg width="16" height="16" viewBox="0 0 24 24"><path fill="white" d="M12 2a7 7 0 0 0-7 7c0 5.25 7 13 7 13s7-7.75 7-13a7 7 0 0 0-7-7zm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5z"/></svg>
    </button>

    <button class="control-btn checks-btn" onclick={() => (appState.showChecks = true)} title="Données à vérifier">
      <svg width="16" height="16" viewBox="0 0 24 24"><path fill="white" d="M9.5 3a6.5 6.5 0 0 1 5.25 10.33l5.46 5.46-1.42 1.42-5.46-5.46A6.5 6.5 0 1 1 9.5 3zm0 2a4.5 4.5 0 1 0 0 9 4.5 4.5 0 0 0 0-9z"/></svg>
      {#if appState.isBackendReady && appState.openChecks.length}
        <span class="badge">{appState.openChecks.length}</span>
      {/if}
    </button>

    <button class="control-btn" onclick={() => (appState.showSettings = true)} title="Réglages">
      <svg width="16" height="16" viewBox="0 0 24 24"><path fill="white" d="M19.14 12.94a7.07 7.07 0 0 0 0-1.88l2.03-1.58a.5.5 0 0 0 .12-.64l-1.92-3.32a.5.5 0 0 0-.61-.22l-2.39.96a7.03 7.03 0 0 0-1.63-.94l-.36-2.54a.5.5 0 0 0-.5-.42h-3.84a.5.5 0 0 0-.5.42l-.36 2.54c-.59.24-1.13.56-1.63.94l-2.39-.96a.5.5 0 0 0-.61.22L2.71 8.84a.5.5 0 0 0 .12.64l2.03 1.58a7.07 7.07 0 0 0 0 1.88l-2.03 1.58a.5.5 0 0 0-.12.64l1.92 3.32c.13.22.39.31.61.22l2.39-.96c.5.38 1.04.7 1.63.94l.36 2.54c.04.24.25.42.5.42h3.84c.25 0 .46-.18.5-.42l.36-2.54c.59-.24 1.13-.56 1.63-.94l2.39.96c.22.09.48 0 .61-.22l1.92-3.32a.5.5 0 0 0-.12-.64l-2.03-1.58zM12 15.5A3.5 3.5 0 1 1 12 8.5a3.5 3.5 0 0 1 0 7z"/></svg>
    </button>

    <button class="control-btn" onclick={() => appState.exportDatabase()} title="Exporter la base de données">
      <svg width="16" height="16" viewBox="0 0 24 24"><path fill="white" d="M13 3h-2v10.17l-3.59-3.58L6 11l6 6l6-6l-1.41-1.41L13 13.17V3zM5 19h14v2H5z"/></svg>
    </button>

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

  .checks-btn {
    position: relative;
  }

  .badge {
    position: absolute;
    top: 6px;
    right: 6px;
    min-width: 15px;
    height: 15px;
    padding: 0 3px;
    border-radius: 999px;
    background: #6366f1;
    color: white;
    font-size: 9px;
    font-weight: 700;
    line-height: 15px;
    text-align: center;
  }

  .control-btn:hover {
    background: #333;
  }

  .control-btn.close:hover {
    background: #e81123; /* Rouge classique Windows au survol */
  }
</style>
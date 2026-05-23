<script lang="ts">
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import { getCurrentWindow } from '@tauri-apps/api/window';
	import { onMount } from 'svelte';
	import TitleBar from '$lib/components/TitleBar.svelte';

	let { children } = $props();

  	const appWindow = getCurrentWindow();
	let isMaximized = $state(false);

	onMount(() => {
		let unlisten: () => void;

		async function setupListener() {
			isMaximized = await appWindow.isMaximized();

			unlisten = await appWindow.onResized(async () => {
				isMaximized = await appWindow.isMaximized();
			});
		}

		setupListener();

		return () => {
			if (unlisten) unlisten();
		}
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<div
	class="app-container"
	class:is-maximized={isMaximized}
>
	<div class="app-shell" class:is-maximized={isMaximized}>
		<TitleBar {isMaximized} />
		
		<main class="flex-1 overflow-y-auto p-4 relative">
			{@render children()}
		</main>
	</div>
</div>

<style>
	:global(body) {
		margin: 0;
		overflow: hidden;
		background: transparent;
	}

	.app-container {
		width: 100vw;
		height: 100vh;
		padding: 4px;
		display: flex;
		background: transparent;
	}

	.app-container.is-maximized {
		padding: 0;
	}

	.app-shell {
		flex: 1;
		display: flex;
		flex-direction: column;
		background-color: #121214;
		border: 1px solid #333;
		border-radius: 8px;
		box-shadow: 0 2px 5px rgba(0, 0, 0, 0.8);
		overflow: hidden;
	}

	.app-shell.is-maximized {
		border-radius: 0;
		border: none;
		box-shadow: none;
	}
</style>

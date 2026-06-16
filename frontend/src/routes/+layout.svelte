<script lang="ts">
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import { dev } from '$app/environment';
	import { getCurrentWindow } from '@tauri-apps/api/window';
	import { onMount } from 'svelte';
	import { check } from '@tauri-apps/plugin-updater';
	import { ask, message } from '@tauri-apps/plugin-dialog';
	import { relaunch } from '@tauri-apps/plugin-process';
	import TitleBar from '$lib/components/TitleBar.svelte';
	import { Command } from '@tauri-apps/plugin-shell';

	let { children } = $props();

  	const appWindow = getCurrentWindow();
	let isMaximized = $state(false);

	async function checkForUpdates(manual: boolean) {
		try {
			const update = await check();
			if (update?.available) {
				const confirmed = await ask(
					`Une version ${update.version} est disponible (publiée le ${update.date}). Voulez-vous l'installer ?`,
					{ title: 'Mise à jour disponible', kind: 'info' }
				);

				if (confirmed) {
					await update.downloadAndInstall();
					await relaunch();
				}
			} else if (manual) {
				await message("Votre version est déjà à jour.", { title: "Pas de mise à jour", kind: "info" });
			}
		} catch (error) {
			console.error("Erreur updater:", error);
		}
	}

	onMount(() => {
		let unlisten: () => void;
		let pythonChild: any;

		async function initializeApp() {
			// Démarrer le backend Python
			if(!dev) {
				try {
					const command = Command.sidecar("bin/allnightlong-backend");
					pythonChild = await command.spawn();
					console.log("Backend démarré avec PID:", pythonChild.pid);
				} catch (error) {
					console.error("Impossible de démarrer le backend:", error);
					// S'il y a un échec, on l'affiche dans un vrai pop-up Windows [1.1.2]
					await message(
						`Erreur lors du démarrage du binaire Python :\n\n${error}`, 
						{ title: 'Erreur Système Backend', kind: 'error' }
					);
				}
			} else {
				console.log("Mode développement : le backend doit être démarré manuellement.");
			}

			// Gérer le resize de la fenêtre
			try {
				isMaximized = await appWindow.isMaximized();
				unlisten = await appWindow.onResized(async () => {
					isMaximized = await appWindow.isMaximized();
				});
			} catch (error) {
				console.error("Erreur lors de l'écoute du redimensionnement:", error);
			}

			// Vérifier les mises à jour
			try {
				await checkForUpdates(false);
			} catch (error) {
				console.error("Erreur lors de la vérification des mises à jour:", error);
			}
		}

		initializeApp();

		return () => {
			if (unlisten) unlisten();
			if (pythonChild) {
				pythonChild.kill();
			}
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

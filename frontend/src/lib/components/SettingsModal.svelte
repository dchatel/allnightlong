<script lang="ts">
	import { appState } from '$lib/state.svelte';
	import { fade } from 'svelte/transition';
	import { open } from '@tauri-apps/plugin-dialog';

	let imagesFolder = $state('');
	let weatherMarginHours = $state(1);
	let saving = $state(false);

	// Copie de travail à chaque ouverture
	$effect(() => {
		if (appState.showSettings) {
			imagesFolder = appState.settings.imagesFolder;
			weatherMarginHours = appState.settings.weatherMarginHours;
		}
	});

	async function browse() {
		const folder = await open({
			directory: true,
			multiple: false,
			title: 'Dossier qui contient vos images',
			defaultPath: imagesFolder || undefined
		});
		if (typeof folder === 'string') imagesFolder = folder;
	}

	async function save() {
		saving = true;
		await appState.saveSettings({ imagesFolder: imagesFolder.trim(), weatherMarginHours: Number(weatherMarginHours) });
		saving = false;
	}

	function close() {
		appState.showSettings = false;
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key !== 'Escape' || !appState.showSettings) return;
		e.stopPropagation();
		close();
	}
</script>

<svelte:window onkeydowncapture={handleKeydown} />

{#if appState.showSettings}
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div transition:fade={{ duration: 150 }} onclick={close} class="fixed inset-0 bg-black/70 backdrop-blur-sm z-60 flex items-center justify-center p-8">
		<div onclick={(e) => e.stopPropagation()} class="bg-[#161619] border border-[#333] rounded-2xl w-full max-w-2xl flex flex-col overflow-hidden shadow-2xl">
			<div class="h-14 border-b border-[#333] bg-[#1a1a1d] px-6 flex items-center justify-between shrink-0 select-none">
				<div class="flex items-center space-x-3">
					<span class="text-xl">⚙</span>
					<h2 class="text-sm font-bold uppercase tracking-widest text-white">Réglages</h2>
				</div>
				<button
					onclick={close}
					class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-surface-800 text-surface-400 hover:text-white transition-colors text-lg"
				>✕</button>
			</div>

			<div class="p-6 flex flex-col gap-6">
				<section class="bg-[#1e1e21] p-4 rounded-lg border border-[#333] space-y-3">
					<span class="text-[10px] uppercase font-bold text-surface-400 block border-b border-[#333] pb-1.5">Images</span>
					<label for="settings-images-folder" class="block text-xs text-white font-bold">Dossier des images</label>
					<div class="flex gap-2">
						<input id="settings-images-folder" type="text" class="form-input flex-1" bind:value={imagesFolder} placeholder="Par exemple E:\Astro" />
						<button onclick={browse} class="btn-secondary text-xs whitespace-nowrap">Parcourir…</button>
					</div>
					<p class="text-[11px] text-surface-400 leading-relaxed">
						Les images ne sont jamais copiées. Celles qui se trouvent dans ce dossier sont enregistrées par leur
						emplacement <em>à l'intérieur</em> du dossier : si le dossier change de place ou de lettre de disque
						(E: devient F:), il suffit de modifier ce réglage pour que toutes les images se retrouvent.
					</p>
				</section>

				<section class="bg-[#1e1e21] p-4 rounded-lg border border-[#333] space-y-3">
					<span class="text-[10px] uppercase font-bold text-surface-400 block border-b border-[#333] pb-1.5">Météo</span>
					<div class="flex items-center gap-3">
						<label for="settings-weather-margin" class="text-xs text-white font-bold">Marge autour du créneau</label>
						<select id="settings-weather-margin" class="form-input" style="width: 6rem" bind:value={weatherMarginHours}>
							{#each [0, 1, 2, 3, 4, 5, 6] as hours (hours)}
								<option value={hours}>{hours} h</option>
							{/each}
						</select>
					</div>
					<p class="text-[11px] text-surface-400 leading-relaxed">
						La météo est récupérée sur Open-Meteo pour le créneau des observations de la nuit, élargi de cette marge
						avant et après. Les valeurs saisies ou corrigées à la main ne sont jamais écrasées.
					</p>
				</section>
			</div>

			<div class="border-t border-[#333] px-6 py-4 flex justify-end gap-2">
				<button onclick={close} class="btn-secondary text-xs">Annuler</button>
				<button onclick={save} disabled={saving} class="btn-primary text-xs disabled:opacity-40">Enregistrer</button>
			</div>
		</div>
	</div>
{/if}

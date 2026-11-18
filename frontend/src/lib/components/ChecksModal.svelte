<script lang="ts">
	import { appState } from '$lib/state.svelte';
	import { RULES, type Check } from '$lib/checks';
	import { fade } from 'svelte/transition';

	// Données à vérifier : signalements groupés par règle, avec accès au rapport et « c'est normal »
	let showDismissed = $state(false);

	// Relevés météo relus à l'ouverture : ils ont pu changer depuis le démarrage
	$effect(() => {
		if (appState.showChecks) appState.loadChecksData();
	});

	let all = $derived(appState.checks);
	let visible = $derived(showDismissed ? all : all.filter(c => !appState.dismissedChecks.includes(c.key)));
	let dismissedCount = $derived(all.length - appState.openChecks.length);
	let groups = $derived(
		Object.entries(RULES)
			.map(([rule, title]) => ({ rule, title, items: visible.filter(c => c.rule === rule) }))
			.filter(g => g.items.length)
	);
	const isDismissed = (c: Check) => appState.dismissedChecks.includes(c.key);

	function close() {
		appState.showChecks = false;
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key !== 'Escape' || !appState.showChecks) return;
		e.stopPropagation();
		close();
	}
</script>

<svelte:window onkeydowncapture={handleKeydown} />

{#if appState.showChecks}
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div transition:fade={{ duration: 150 }} onclick={close} class="fixed inset-0 bg-black/70 backdrop-blur-sm z-60 flex items-center justify-center p-8">
		<div onclick={(e) => e.stopPropagation()} class="bg-[#161619] border border-[#333] rounded-2xl w-full max-w-4xl max-h-[85vh] flex flex-col overflow-hidden shadow-2xl">
			<div class="h-14 border-b border-[#333] bg-[#1a1a1d] px-6 flex items-center justify-between shrink-0 select-none">
				<div class="flex items-center space-x-3">
					<span class="text-xl">🔎</span>
					<h2 class="text-sm font-bold uppercase tracking-widest text-white">Données à vérifier</h2>
					<span class="text-xs text-surface-400 normal-case">{appState.openChecks.length} à examiner</span>
				</div>
				<button onclick={close} class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-surface-800 text-surface-400 hover:text-white transition-colors text-lg">✕</button>
			</div>

			<div class="px-6 py-3 border-b border-[#2a2a2d] flex items-center justify-between gap-4 text-[11px] text-surface-400">
				<span>Repérées par des règles simples. Corrigez le rapport, ou marquez « c'est normal » pour ne plus le voir ici.</span>
				{#if dismissedCount}
					<label class="flex items-center gap-1.5 whitespace-nowrap cursor-pointer">
						<input type="checkbox" bind:checked={showDismissed} />
						Afficher les {dismissedCount} marqués normaux
					</label>
				{/if}
			</div>

			<div class="flex-1 overflow-y-auto p-6 space-y-6">
				{#if groups.length === 0}
					<p class="text-sm text-surface-400 text-center py-10">Rien à vérifier. ✓</p>
				{/if}
				{#each groups as group (group.rule)}
					<section>
						<h3 class="text-[11px] uppercase font-bold tracking-wider text-surface-300 border-b border-[#333] pb-1.5 mb-2">
							{group.title} <span class="text-surface-500 font-normal">({group.items.length})</span>
						</h3>
						<ul class="space-y-1.5">
							{#each group.items as check (check.key)}
								<li class="flex items-start gap-3 bg-[#1e1e21] border border-[#2a2a2d] rounded-lg px-3 py-2" class:opacity-50={isDismissed(check)}>
									<div class="flex-1 min-w-0">
										<span class="block text-xs font-bold text-white">{check.title}</span>
										<span class="block text-[11px] text-surface-300">{check.detail}</span>
									</div>
									<div class="flex items-center gap-2 shrink-0">
										{#each check.observationIds.slice(0, 2) as id, n (id)}
											<button type="button" onclick={() => appState.openObservationFromChecks(id)} class="btn-secondary text-[11px]">
												{check.observationIds.length > 1 ? `Rapport ${n + 1}` : 'Ouvrir le rapport'}
											</button>
										{/each}
										<button
											type="button"
											onclick={() => appState.setCheckDismissed(check.key, !isDismissed(check))}
											class="text-[11px] font-bold text-indigo-400 hover:text-indigo-300 whitespace-nowrap"
										>{isDismissed(check) ? 'Remettre à vérifier' : "C'est normal"}</button>
									</div>
								</li>
							{/each}
						</ul>
					</section>
				{/each}
			</div>
		</div>
	</div>
{/if}

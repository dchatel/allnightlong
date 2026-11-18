<script lang="ts">
	import { appState, type WeatherReading } from '$lib/state.svelte';

	// Tableau des relevés de la nuit, modifiable. Une valeur Open-Meteo corrigée est marquée « modifiée »
	// et n'est plus touchée par le rafraîchissement ; les lignes collées ou ajoutées le sont d'emblée.
	let { sessionId, nightDate, readings }: { sessionId: number; nightDate: string; readings: WeatherReading[] } = $props();

	const SOURCES: Record<string, string> = { 'open-meteo': 'Open-Meteo', meteoblue: 'meteoblue', manuel: 'Saisie' };
	const COLUMNS: { field: keyof WeatherReading; label: string; digits: number }[] = [
		{ field: 'cloudLow', label: 'Bas %', digits: 0 },
		{ field: 'cloudMid', label: 'Moy. %', digits: 0 },
		{ field: 'cloudHigh', label: 'Haut %', digits: 0 },
		{ field: 'seeing', label: 'Seeing ″', digits: 2 },
		{ field: 'index1', label: 'Idx 1', digits: 0 },
		{ field: 'index2', label: 'Idx 2', digits: 0 },
		{ field: 'jetStream', label: 'Jet m/s', digits: 0 },
		{ field: 'temp', label: 'Temp °C', digits: 1 },
		{ field: 'humidity', label: 'Hum. %', digits: 0 },
		{ field: 'dewPoint', label: 'Rosée °C', digits: 1 }
	];

	let editing = $state(false);
	let draft = $state<WeatherReading[]>([]);
	let pasteOpen = $state(false);
	let pasteText = $state('');
	let pasteMessage = $state('');
	let saving = $state(false);

	function startEdit() {
		draft = $state.snapshot(readings) as WeatherReading[];
		pasteOpen = false;
		pasteMessage = '';
		editing = true;
	}

	function setValue(row: WeatherReading, field: keyof WeatherReading, text: string) {
		const value = text.trim() === '' ? null : Number(text.replace(',', '.'));
		(row as any)[field] = Number.isFinite(value as number) ? value : null;
		row.edited = true;
	}

	// Heure saisie "HH:MM" : avant midi, elle appartient au lendemain de la nuit
	function setTime(row: WeatherReading, text: string) {
		const match = text.trim().match(/^(\d{1,2})[:h](\d{2})$/);
		if (!match || Number(match[1]) > 23 || Number(match[2]) > 59) return;
		const hour = Number(match[1]);
		const day = new Date(`${nightDate}T00:00:00Z`);
		if (hour < 12) day.setUTCDate(day.getUTCDate() + 1);
		row.time = `${day.toISOString().slice(0, 10)} ${String(hour).padStart(2, '0')}:${match[2]}`;
		row.edited = true;
	}

	function addRow() {
		const last = draft.at(-1)?.time;
		const next = last ? new Date(last.replace(' ', 'T') + 'Z') : new Date(`${nightDate}T20:00:00Z`);
		if (last) next.setUTCHours(next.getUTCHours() + 1);
		draft = [...draft, {
			time: next.toISOString().slice(0, 16).replace('T', ' '),
			cloudLow: null, cloudMid: null, cloudHigh: null, seeing: null, index1: null, index2: null,
			jetStream: null, temp: null, humidity: null, dewPoint: null, source: 'manuel', edited: true
		}];
	}

	// Les lignes collées remplacent celles de la même heure
	async function paste() {
		const parsed = await appState.parseMeteoblue(pasteText, nightDate);
		if (parsed.length === 0) {
			pasteMessage = 'Aucune ligne reconnue. Format attendu : 21h00 TU ( 34-0-0 / 1.39 / 4-2 / 16ms / 13°C / 91% )';
			return;
		}
		const times = new Set(parsed.map(r => r.time));
		draft = [...draft.filter(r => !times.has(r.time)), ...parsed].sort((a, b) => a.time.localeCompare(b.time));
		pasteMessage = '';
		pasteText = '';
		pasteOpen = false;
	}

	async function save() {
		saving = true;
		const sorted = [...draft].sort((a, b) => a.time.localeCompare(b.time));
		if (await appState.saveWeather(sessionId, sorted)) editing = false;
		saving = false;
	}

	const format = (v: unknown, digits: number) => (v == null ? '—' : (v as number).toFixed(digits));
	let rows = $derived(editing ? draft : readings);
</script>

<div class="flex flex-wrap items-center justify-end gap-2 mb-2">
	{#if editing}
		<button type="button" onclick={() => (pasteOpen = !pasteOpen)} class="btn-secondary text-xs">Coller une ligne meteoblue</button>
		<button type="button" onclick={addRow} class="btn-secondary text-xs">+ Relevé</button>
		<button type="button" onclick={() => (editing = false)} class="btn-secondary text-xs">Annuler</button>
		<button type="button" onclick={save} disabled={saving} class="btn-primary text-xs disabled:opacity-40">Enregistrer les relevés</button>
	{:else}
		<button type="button" onclick={startEdit} class="btn-secondary text-xs">Modifier les relevés</button>
	{/if}
</div>

{#if editing && pasteOpen}
	<div class="mb-3 bg-[#17171a] border border-[#333] rounded-lg p-3 space-y-2">
		<label for="meteoblue-paste" class="block text-[10px] text-surface-400">
			Une ou plusieurs lignes, au format des notes. Une ligne remplace le relevé de la même heure.
		</label>
		<textarea
			id="meteoblue-paste"
			class="form-input min-h-20 py-2 font-mono text-xs"
			placeholder="21h00 TU ( 34-0-0 / 1.39 / 4-2 / 16ms / 13°C / 91% )"
			bind:value={pasteText}
		></textarea>
		{#if pasteMessage}<p class="text-[11px] text-yellow-500">{pasteMessage}</p>{/if}
		<div class="flex justify-end">
			<button type="button" onclick={paste} disabled={!pasteText.trim()} class="btn-primary text-xs disabled:opacity-40">Ajouter</button>
		</div>
	</div>
{/if}

{#if rows.length === 0}
	<p class="text-xs text-surface-500">Aucun relevé pour cette nuit.</p>
{:else}
	<div class="overflow-x-auto">
		<table class="w-full text-xs text-right tabular-nums">
			<thead>
				<tr class="text-[10px] text-surface-400">
					<th class="text-left font-normal pb-1">Heure TU</th>
					{#each COLUMNS as c (c.field)}<th class="font-normal px-1">{c.label}</th>{/each}
					<th class="font-normal pl-2">Source</th>
					{#if editing}<th></th>{/if}
				</tr>
			</thead>
			<tbody class="text-white">
				{#each rows as r, i (editing ? i : r.time)}
					<tr class="border-t border-[#2a2a2d]" class:marked={r.edited || r.source !== 'open-meteo'}>
						<td class="text-left py-0.5">
							{#if editing}
								<input type="text" class="cell w-14 text-left" value={r.time.slice(11, 16)} onchange={(e) => setTime(r, e.currentTarget.value)} />
							{:else}
								{r.time.slice(11, 16)}
							{/if}
						</td>
						{#each COLUMNS as c (c.field)}
							<td class="px-1">
								{#if editing}
									<input type="text" inputmode="decimal" class="cell w-12" value={r[c.field] ?? ''} onchange={(e) => setValue(r, c.field, e.currentTarget.value)} />
								{:else}
									{format(r[c.field], c.digits)}
								{/if}
							</td>
						{/each}
						<td class="text-surface-400 pl-2 whitespace-nowrap">{SOURCES[r.source] ?? r.source}{r.edited ? ' ✎' : ''}</td>
						{#if editing}
							<td class="pl-1">
								<button type="button" title="Supprimer ce relevé" onclick={() => (draft = draft.filter((_, n) => n !== i))} class="text-red-400 hover:text-red-300">✕</button>
							</td>
						{/if}
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
	<p class="text-[10px] text-surface-500 mt-2">
		<span class="legend-mark"></span> relevé saisi, collé ou corrigé : le rafraîchissement depuis Open-Meteo ne le modifie pas.
	</p>
{/if}

<style>
	.marked td:first-child {
		box-shadow: inset 3px 0 0 #6366f1;
		padding-left: 6px;
	}
	.legend-mark {
		display: inline-block;
		width: 3px;
		height: 10px;
		background: #6366f1;
		vertical-align: middle;
		margin-right: 4px;
	}
	.cell {
		background: #202024;
		border: 1px solid #333;
		border-radius: 3px;
		padding: 1px 4px;
		text-align: right;
		color: #e2e8f0;
	}
	.cell:focus {
		outline: none;
		border-color: #6366f1;
	}
</style>

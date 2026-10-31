import { readFileSync, writeFileSync } from 'fs';
import { execSync } from 'child_process';

// L'argument passé à la commande (ex: patch, minor, major, ou "0.1.8")
const arg = process.argv[2]; 
if (!arg) {
    console.error("❌ ERREUR : Précisez une version. (ex: node release.mjs patch | minor | 0.1.8)");
    process.exit(1);
}

try {
    console.log(`🚀 Démarrage du processus de Release : ${arg}...`);

    // 1. Mise à jour de package.json via npm
    console.log(`\n📦 1. Mise à jour de package.json...`);
    execSync(`npm version ${arg} --no-git-tag-version`, { cwd: './frontend', stdio: 'inherit' });

    // 2. Lecture de la nouvelle version
    const pkg = JSON.parse(readFileSync('./frontend/package.json', 'utf8'));
    const newVersion = pkg.version;
    console.log(`Nouvelle version détectée : v${newVersion}`);

    // 3. Synchronisation de tauri.conf.json
    console.log(`\n🦀 2. Synchronisation de tauri.conf.json...`);
    const tauriPath = './frontend/src-tauri/tauri.conf.json';
    const tauriConf = JSON.parse(readFileSync(tauriPath, 'utf8'));
    tauriConf.version = newVersion;
    writeFileSync(tauriPath, JSON.stringify(tauriConf, null, 2) + '\n');

    // 4. Synchronisation de Cargo.toml
    console.log(`\n⚙️ 3. Synchronisation de Cargo.toml...`);
    const cargoPath = './frontend/src-tauri/Cargo.toml';
    let cargo = readFileSync(cargoPath, 'utf8');
    // Remplace la ligne version = "..." par la nouvelle
    cargo = cargo.replace(/^version\s*=\s*".*"/m, `version = "${newVersion}"`);
    writeFileSync(cargoPath, cargo);
    // Répercute la nouvelle version dans Cargo.lock, sans toucher aux dépendances
    execSync('cargo update --workspace --offline', { cwd: './frontend/src-tauri', stdio: 'inherit' });

    // 5. Commandes Git automatiques
    console.log(`\n☁️ 4. Envoi sur GitHub...`);
    execSync('git add .', { stdio: 'inherit' });
    execSync(`git commit -m "v${newVersion}"`, { stdio: 'inherit' });
    execSync(`git tag v${newVersion}`, { stdio: 'inherit' });
    execSync('git push', { stdio: 'inherit' });
    execSync('git push --tags', { stdio: 'inherit' });

    console.log(`\n🎉 SUCCÈS ! La version v${newVersion} est publiée et en cours de compilation sur GitHub Actions.`);
} catch (error) {
    console.error("\n❌ Une erreur est survenue :", error.message);
}
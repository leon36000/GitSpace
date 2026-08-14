use gs_foundry_cli::{
    NativeFoundry, NativeScenario, RunReceipt, receipt_bytes, replay_bytes,
};
use std::{env, fs, io::{self, Write}, path::PathBuf, process::ExitCode};

fn main() -> ExitCode {
    match execute(env::args().skip(1).collect()) {
        Ok(bytes) => {
            let mut stdout = io::stdout().lock();
            if stdout.write_all(&bytes).is_err() || stdout.write_all(b"\n").is_err() {
                return ExitCode::FAILURE;
            }
            ExitCode::SUCCESS
        }
        Err(message) => {
            eprintln!("{message}");
            ExitCode::FAILURE
        }
    }
}

fn execute(args: Vec<String>) -> Result<Vec<u8>, String> {
    let Some(command) = args.first().map(String::as_str) else {
        return Err(usage());
    };
    match command {
        "run" => run_command(&args[1..]),
        "replay" => replay_command(&args[1..]),
        _ => Err(usage()),
    }
}

fn run_command(args: &[String]) -> Result<Vec<u8>, String> {
    let root = required_flag(args, "--root")?;
    let scenario = required_flag(args, "--scenario")?;
    let source_commit = required_flag(args, "--source-commit")?;
    ensure_exact_flags(args, &["--root", "--scenario", "--source-commit"])?;
    let scenario = NativeScenario::parse(&scenario)
        .ok_or_else(|| "scenario must be one of pass|fail|timeout|policy|infra".to_owned())?;
    let foundry = NativeFoundry::open(PathBuf::from(root), source_commit)
        .map_err(|error| error.to_string())?;
    let receipt = foundry.run(scenario).map_err(|error| error.to_string())?;
    receipt_bytes(&receipt).map_err(|error| error.to_string())
}

fn replay_command(args: &[String]) -> Result<Vec<u8>, String> {
    let root = required_flag(args, "--root")?;
    let receipt_path = required_flag(args, "--receipt")?;
    ensure_exact_flags(args, &["--root", "--receipt"])?;
    let bytes = fs::read(&receipt_path)
        .map_err(|error| format!("failed to read receipt {receipt_path}: {error}"))?;
    let receipt: RunReceipt = serde_json::from_slice(&bytes)
        .map_err(|error| format!("invalid receipt JSON: {error}"))?;
    let foundry = NativeFoundry::open(PathBuf::from(root), receipt.source_commit.clone())
        .map_err(|error| error.to_string())?;
    let report = foundry.replay(&receipt).map_err(|error| error.to_string())?;
    replay_bytes(&report).map_err(|error| error.to_string())
}

fn required_flag(args: &[String], name: &str) -> Result<String, String> {
    let Some(index) = args.iter().position(|value| value == name) else {
        return Err(format!("missing required flag {name}\n{}", usage()));
    };
    args.get(index + 1)
        .filter(|value| !value.starts_with("--"))
        .cloned()
        .ok_or_else(|| format!("missing value for {name}"))
}

fn ensure_exact_flags(args: &[String], allowed: &[&str]) -> Result<(), String> {
    if args.len() != allowed.len() * 2 {
        return Err(usage());
    }
    for pair in args.chunks_exact(2) {
        if !allowed.contains(&pair[0].as_str()) || pair[1].starts_with("--") {
            return Err(usage());
        }
    }
    Ok(())
}

fn usage() -> String {
    "usage:\n  gs-foundry-cli run --root <path> --scenario <pass|fail|timeout|policy|infra> --source-commit <hex>\n  gs-foundry-cli replay --root <path> --receipt <receipt.json>".to_owned()
}

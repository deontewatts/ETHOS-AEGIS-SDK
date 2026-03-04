//! aegis-guard — CLI guard tool
//!
//! Reads a payload from stdin or args and exits 0 (safe) or 1 (condemned).
//!
//! Usage:
//!   echo "user message" | aegis-guard
//!   aegis-guard "inline payload here"

use ethos_aegis_sdk::{AegisClient, ClientOptions, Transport};
use std::io::Read;

fn main() {
    let payload = if let Some(arg) = std::env::args().nth(1) {
        arg
    } else {
        let mut buf = String::new();
        std::io::stdin().read_to_string(&mut buf).unwrap_or(0);
        buf.trim().to_string()
    };

    if payload.is_empty() {
        eprintln!("Usage: aegis-guard \"payload\" OR echo \"payload\" | aegis-guard");
        std::process::exit(2);
    }

    let client = AegisClient::new(ClientOptions {
        transport: Transport::Subprocess,
        verbose:   true,
        ..Default::default()
    });

    match client.adjudicate(&payload, None) {
        Ok(v) => {
            if v.condemned {
                eprintln!("[CONDEMNED] depth={} maligna={}", v.depth, v.maligna_count);
                std::process::exit(1);
            } else {
                println!("[SANCTIFIED] depth={}", v.depth);
                std::process::exit(0);
            }
        }
        Err(e) => {
            eprintln!("[ERROR] {e}");
            std::process::exit(2);
        }
    }
}

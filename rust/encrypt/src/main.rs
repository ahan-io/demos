use ring::error::Unspecified;
use ring::rand::SecureRandom;
use ring::rand::SystemRandom;
use ring::aead::AES_256_GCM;
use ring::aead::UnboundKey;
use ring::aead::BoundKey;
use ring::aead::SealingKey;
use ring::aead::OpeningKey;
use ring::aead::Aad;
use ring::aead::NonceSequence;
use ring::aead::NONCE_LEN;
use ring::aead::Nonce;

// Always returns the same nonce value for simplicity, don't use for more than 1 sealing operation!
struct SingleNonceSequence([u8; NONCE_LEN]);

impl NonceSequence for SingleNonceSequence {
    fn advance(&mut self) -> Result<Nonce, Unspecified> {
        Nonce::try_assume_unique_for_key(&self.0)
    }
}

fn main() -> Result<(), Unspecified> {
    // Encrypt and decrypt some data using AES-GCM-256

    // 加密过程
    let rand = SystemRandom::new();

    let mut key_bytes = vec![0; AES_256_GCM.key_len()];
    rand.fill(&mut key_bytes)?;
    let mut nonce_value = [0; NONCE_LEN];
    rand.fill(&mut nonce_value)?;

    let unbound_key = UnboundKey::new(&AES_256_GCM, &key_bytes)?;
    let nonce_sequence = SingleNonceSequence(nonce_value);
    // sealing_key 用于加密
    let mut sealing_key = SealingKey::new(unbound_key, nonce_sequence);

    let associated_data = Aad::from(b"additional public data");
    let data = b"hello world";
    let mut in_out = data.clone();
    let tag = sealing_key.seal_in_place_separate_tag(associated_data, &mut in_out)?;

    // 解密过程
    let unbound_key = UnboundKey::new(&AES_256_GCM, &key_bytes)?;
    let nonce_sequence = SingleNonceSequence(nonce_value);
    // opening_key 用于解密
    let mut opening_key = OpeningKey::new(unbound_key, nonce_sequence);

    let associated_data = Aad::from(b"additional public data");
    let mut cypher_text_with_tag = [&in_out, tag.as_ref()].concat();
    let decrypted_data = opening_key.open_in_place(associated_data, &mut cypher_text_with_tag)?;

    assert_eq!(data, decrypted_data);

    println!("hahaha");
    Ok(())

    
}
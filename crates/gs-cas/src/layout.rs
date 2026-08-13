use crate::{safety::validate_directory, CasError, Digest};
use std::{
    fs,
    path::{Path, PathBuf},
};

#[derive(Debug)]
pub struct LocalCas {
    pub(crate) root: PathBuf,
    pub(crate) objects: PathBuf,
    pub(crate) temporary: PathBuf,
}

impl LocalCas {
    pub fn open(root: impl AsRef<Path>) -> Result<Self, CasError> {
        let requested = root.as_ref();
        fs::create_dir_all(requested)
            .map_err(|source| CasError::io("create store root", requested, source))?;
        let root = fs::canonicalize(requested)
            .map_err(|source| CasError::io("canonicalize store root", requested, source))?;
        validate_directory(&root)?;

        let objects_root = root.join("objects");
        fs::create_dir_all(&objects_root)
            .map_err(|source| CasError::io("create objects root", &objects_root, source))?;
        validate_directory(&objects_root)?;

        let objects = objects_root.join("sha256");
        fs::create_dir_all(&objects)
            .map_err(|source| CasError::io("create object namespace", &objects, source))?;
        validate_directory(&objects)?;

        let temporary = root.join("tmp");
        fs::create_dir_all(&temporary)
            .map_err(|source| CasError::io("create temporary root", &temporary, source))?;
        validate_directory(&temporary)?;

        Ok(Self {
            root,
            objects,
            temporary,
        })
    }

    pub fn root(&self) -> &Path {
        &self.root
    }

    pub fn object_path(&self, digest: &Digest) -> PathBuf {
        let hex = digest_hex(digest);
        self.objects.join(&hex[..2]).join(&hex[2..])
    }
}

pub(crate) fn digest_hex(digest: &Digest) -> String {
    const HEX: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(64);
    for byte in digest.as_bytes() {
        output.push(HEX[(byte >> 4) as usize] as char);
        output.push(HEX[(byte & 0x0f) as usize] as char);
    }
    output
}

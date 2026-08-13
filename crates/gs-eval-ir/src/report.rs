use std::{error::Error, fmt};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ValidationIssue {
    pub path: String,
    pub code: String,
    pub message: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ValidationReport {
    pub(crate) issues: Vec<ValidationIssue>,
}

impl ValidationReport {
    pub fn issues(&self) -> &[ValidationIssue] {
        &self.issues
    }

    pub(crate) fn single(path: impl Into<String>, code: impl Into<String>, message: impl Into<String>) -> Self {
        Self { issues: vec![ValidationIssue { path: path.into(), code: code.into(), message: message.into() }] }
    }

    pub(crate) fn type_mismatch() -> Self {
        Self::single("/", "internal.type_mismatch", "validated schema decoded into the wrong IR variant")
    }
}

impl fmt::Display for ValidationReport {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        for (index, issue) in self.issues.iter().enumerate() {
            if index > 0 { formatter.write_str("; ")?; }
            write!(formatter, "{} [{}]: {}", issue.path, issue.code, issue.message)?;
        }
        Ok(())
    }
}

impl Error for ValidationReport {}

#!/bin/bash

# Install NCBI EDirect tools into the edirect/ directory of this repository.
# Run from the repository root: bash edirect/install-edirect.sh
#
# Adapted from the official NCBI EDirect install script (public domain):
# https://www.ncbi.nlm.nih.gov/books/NBK179288/#chapter6.Public_Domain_Notice
# Original installs to ~/edirect; this version targets the repo's edirect/ folder.

base="https://ftp.ncbi.nlm.nih.gov/entrez/entrezdirect"

FetchFile() {
  fl="$1"
  if [ -x "$(command -v curl)" ]
  then
    curl -s "${base}/${fl}" -o "${fl}"
  elif [ -x "$(command -v wget)" ]
  then
    wget "${base}/${fl}"
  else
    echo "Missing curl and wget commands, unable to download EDirect archive" >&2
    exit 1
  fi
}

# Install into the edirect/ directory of this repository (parent of this script).
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EDIRECT_DIR="${REPO_ROOT}/edirect"
mkdir -p "$EDIRECT_DIR"
cd "$REPO_ROOT"

# Download and extract edirect archive into edirect/
FetchFile "edirect.tar.gz"
if [ -s "edirect.tar.gz" ]
then
  gunzip -c edirect.tar.gz | tar xf -
  rm edirect.tar.gz
fi
if [ ! -d "edirect" ]
then
  echo "Unable to download EDirect archive" >&2
  exit 1
fi

cd edirect
DIR=$(pwd)

# Detect platform and fetch precompiled binaries.
plt=""
alt=""
osname=$(uname -s)
cputype=$(uname -m)
case "$osname-$cputype" in
  Linux-x86_64 )    plt=Linux ;;
  Darwin-x86_64 )   plt=Darwin; alt=Silicon ;;
  Darwin-*arm* )    plt=Silicon; alt=Darwin ;;
  CYGWIN_NT-* | MINGW*-* ) plt=CYGWIN_NT ;;
  Linux-*arm* )     plt=ARM ;;
  Linux-aarch64 )   plt=ARM64 ;;
  * )
    echo "Unrecognized platform: $osname-$cputype"
    exit 1
    ;;
esac

if [ -n "$plt" ]
then
  for exc in xtract rchive transmute
  do
    FetchFile "$exc.$plt.gz"
    gunzip -f "$exc.$plt.gz"
    chmod +x "$exc.$plt"
    if [ -n "$alt" ]
    then
      FetchFile "$exc.$alt.gz"
      gunzip -f "$exc.$alt.gz"
      chmod +x "$exc.$alt"
    fi
  done
fi

echo ""
echo "EDirect installed to: ${DIR}"
echo ""
echo "Add the following to your shell profile (~/.bashrc or ~/.zshrc):"
echo ""
echo "  export PATH=\"${DIR}:\${PATH}\""
echo ""
echo "Or for this session only:"
echo "  export PATH=\"${DIR}:\${PATH}\""

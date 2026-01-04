{ stdenv, fetchFromGitHub, pkg-config, lib
, libGLU, libGL, freeglut, plib
, libvorbis, libogg
, openal, freealut
, libpng, zlib
, libX11, libXi, libXmu, libXrender, libXrandr
, libICE, libSM, libXt, libXxf86vm
, glib
}:

stdenv.mkDerivation rec {
  pname = "torcs";
  version = "1.3.7-scr";

  src = fetchFromGitHub {
    owner = "fmirus";
    repo = "torcs-1.3.7";
    rev = "master";
    sha256 = "sha256-ocXL1qEfFfH5AWnaTl7I/sQ9vhcK1JNxrsL7FTktAu4=";
  };

  nativeBuildInputs = [
    pkg-config
    stdenv.cc
  ];

  buildInputs = [
    libGLU libGL freeglut
    plib
    libvorbis libogg
    openal freealut
    libpng zlib
    libX11 libXi libXmu libXrender libXrandr
    libICE libSM libXt libXxf86vm
    glib
  ];

  # Disable format-security hardening; TORCS has old code that triggers this
  hardeningDisable = [ "format" ];

  configureFlags = [
    "--prefix=${placeholder "out"}"
    "--datadir=${placeholder "out"}/share"
  ];

  # TORCS build flags for compatibility
  preConfigure = ''
    export CFLAGS="-fPIC"
    export CPPFLAGS="$CFLAGS"
    export CXXFLAGS="$CFLAGS"
  '';
  
  postInstall = ''
    # Install data files using make's data installation if available
    # Fall back to manual copy if not
    if make -n datainstall >/dev/null 2>&1; then
      make datainstall
    else
      echo "Manual data installation..."
      # Copy runtime data files
      if [ -d "data" ]; then
        mkdir -p $out/share/games/torcs
        cp -r data $out/share/games/torcs/
      fi
      # Also check for runtime-data directory from the build
      if [ -d "runtime" ]; then
        cp -r runtime/* $out/share/games/torcs/ || true
      fi
    fi
    
    # Fix rpath for torcs-bin so it can find its libraries
    # This is critical for gym-torcs which may call torcs-bin directly
    if [ -f "$out/lib/torcs/bin/torcs-bin" ]; then
      echo "Fixing rpath for torcs-bin..."
      patchelf --set-rpath "$out/lib/torcs/lib:${lib.makeLibraryPath [ libGL libGLU freeglut plib openal freealut libpng zlib libX11 libXi libXmu libXrender libXrandr ]}" \
        "$out/lib/torcs/bin/torcs-bin"
    fi
    
    # Fix hardcoded /bin/bash shebang in wrapper script
    for script in $out/bin/*; do
      if [ -f "$script" ]; then
        substituteInPlace "$script" \
          --replace-warn '/bin/bash' '${stdenv.shell}'
      fi
    done
    
    # Ensure the wrapper script points to the correct data directory
    # The TORCS wrapper expects DATADIR to point to share/games/torcs
    if [ -f "$out/bin/torcs" ]; then
      substituteInPlace "$out/bin/torcs" \
        --replace-warn 'DATADIR=$prefix/share/games/torcs' "DATADIR=$out/share/games/torcs" || true
    fi
    
    # Fix permissions on all installed files
    chmod -R u+w $out/share || true
  '';

  meta = {
    description = "The Open Racing Car Simulator with SCR (Simulated Car Racing) patch";
    homepage = "https://github.com/fmirus/torcs-1.3.7";
    license = lib.licenses.gpl2;
    platforms = lib.platforms.linux;
  };
}

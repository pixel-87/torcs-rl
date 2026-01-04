{ mkShell, callPackage, stdenv, zlib, lib, libGL, libGLU, mesa, ... }:
let
  package = callPackage ./default.nix { };
in
mkShell {
  inherit (package.passthru.devTooling) packages env;
  
  nativeBuildInputs = [
    stdenv.cc
    zlib
    libGL
    libGLU
    mesa
  ];
  
  shellHook = ''
    export LD_LIBRARY_PATH=${lib.makeLibraryPath [stdenv.cc.cc zlib libGL libGLU mesa]}:$LD_LIBRARY_PATH
    export LIBGL_ALWAYS_SOFTWARE=1
  '';
}

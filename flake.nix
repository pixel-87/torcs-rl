{
  description = "TORCS Reinforcement Learning with UV and Nix";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixpkgs-unstable";
  };

  outputs =
    { self, nixpkgs }:
    let
      forAllSystems =
        function:
        nixpkgs.lib.genAttrs nixpkgs.lib.systems.flakeExposed (
          system: function nixpkgs.legacyPackages.${system}
        );
    in
    {
      packages = forAllSystems (pkgs: {
        torcs-rl = pkgs.callPackage ./nix/default.nix { };
        default = self.packages.${pkgs.stdenv.hostPlatform.system}.torcs-rl;
      });

      devShells = forAllSystems (pkgs: {
        default = pkgs.callPackage ./nix/shell.nix { };
      });

      overlays.default = final: _: { torcs-rl = final.callPackage ./nix/default.nix { }; };
    };
}

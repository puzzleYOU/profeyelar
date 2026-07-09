{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";
    flake-utils.url = "github:numtide/flake-utils";
    nix-utils = {
      url = "git+https://gitea.puzzleyou.net/puzzleyou/nix-utils";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, nix-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in with pkgs; {
        devShell = mkShell {
          buildInputs = [
            libmysqlclient
            pkg-config

            (pkgs.python313.withPackages (ps: [
              ps.pip
              ps.build
              ps.tkinter
              ps.setuptools
              ps.requests
              ps.memray
            ]))
          ];
        };
      }
    );
}

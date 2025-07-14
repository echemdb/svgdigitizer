{
  description = "Nix flake for echemdb/svgdigitizer";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable"; # switch to stable when dependencies available
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        pyPkgs = pkgs.python313Packages;
         
         # temporary: remove when available in repository
         svgpathtools = pyPkgs.buildPythonPackage rec {
          pname = "svgpathtools";
          version = "1.7.1";
          pyproject = true;

          src = pkgs.fetchFromGitHub {
            owner = "mathandy";
            repo = "svgpathtools";
            tag = "v${version}";
            hash = "sha256-SzYssDJ+uGb5zXZ16XaMCvIPF8BKJ4VVI/gUghz1IyA=";
          };

          build-system = [ pyPkgs.setuptools ];
          dependencies = [ pyPkgs.numpy pyPkgs.scipy pyPkgs.svgwrite ];
          nativeCheckInputs = [ pyPkgs.pytestCheckHook ];
          pythonImportsCheck = [ "svgpathtools" ];
        };

        svgdigitizer = pyPkgs.buildPythonPackage {
          pname = "svgdigitizer";
          version = "unstable";
          src = ./.;
          format = "pyproject";

          nativeBuildInputs = with pyPkgs; [ setuptools wheel ];
          propagatedBuildInputs = with pyPkgs; [
            astropy
            click
            frictionless
            matplotlib
            mergedeep
            pandas
            pillow
            pybtex
            pymupdf
            pytest
            pyyaml
            scipy
            svg-path
            svgpathtools
            svgwrite
          ];
          nativeCheckInputs = with pyPkgs; [ pytest pytest-xdist ];
          doCheck = true;
          checkPhase = ''
            export MPLBACKEND=Agg
            pytest -n auto --doctest-modules svgdigitizer
          '';
          pythonImportsCheck = [ "svgdigitizer" ];
        };
      in
      {
        packages.default = svgdigitizer;
        packages.svgdigitizer = svgdigitizer;

        devShells.default = pkgs.mkShell {
          buildInputs = with pyPkgs; [
            astropy
            click
            frictionless
            matplotlib
            mergedeep
            pandas
            pillow
            pybtex
            pymupdf
            pytest
            pyyaml
            scipy
            svg-path
            svgpathtools
            svgwrite
          ];
          shellHook = ''
            echo "🐍 DevShell ready for svgdigitizer + svgpathtools"
          '';
        };
      });
}

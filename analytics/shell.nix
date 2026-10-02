{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = [
    (pkgs.python3.withPackages (ps: with ps; [
      fastapi
      uvicorn
      sqlalchemy
      psycopg2
      httpx
      pydantic
      python-dotenv
    ]))
  ];
}

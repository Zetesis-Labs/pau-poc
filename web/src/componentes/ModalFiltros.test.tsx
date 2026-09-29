// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { useState } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { type Filtros, indexar } from "~/dominio/banco";
import { pregunta } from "~/dominio/fixtures";
import { ModalFiltros } from "./ModalFiltros";

const madrid = pregunta({ id: "madrid" });
const valencia = pregunta({
  id: "valencia",
  examen: { ...madrid.examen, id: "valencia", region: "Comunidad Valenciana" },
});
const preguntas = indexar([madrid, valencia]);

beforeEach(() => {
  Object.defineProperties(HTMLDialogElement.prototype, {
    showModal: {
      configurable: true,
      value(this: HTMLDialogElement) {
        this.setAttribute("open", "");
      },
    },
    close: {
      configurable: true,
      value(this: HTMLDialogElement) {
        this.removeAttribute("open");
      },
    },
  });
});

afterEach(() => cleanup());

function BancoPrueba({
  inicial = {},
  onAplicar = vi.fn(),
}: {
  inicial?: Filtros;
  onAplicar?: (filtros: Filtros) => void;
}) {
  const [abierto, setAbierto] = useState(false);
  const [filtros, setFiltros] = useState(inicial);

  return (
    <>
      <button type="button" onClick={() => setAbierto(true)}>
        Abrir filtros
      </button>
      <output data-testid="filtros-aplicados">{JSON.stringify(filtros)}</output>
      <ModalFiltros
        abierto={abierto}
        preguntas={preguntas}
        filtros={filtros}
        consulta=""
        onAplicar={(siguientes) => {
          setFiltros(siguientes);
          onAplicar(siguientes);
        }}
        onCerrar={() => setAbierto(false)}
      />
    </>
  );
}

const abrir = () => {
  const boton = screen.getByRole("button", { name: "Abrir filtros" });
  boton.focus();
  fireEvent.click(boton);
  return screen.getByRole("dialog", { name: "Filtros" });
};

const elegirMadrid = () => {
  const region = screen.getByRole("region", { name: "Región" });
  fireEvent.click(within(region).getByRole("button", { name: /Madrid/ }));
};

describe("ModalFiltros", () => {
  it("abre el diálogo con el recuento actual y devuelve el foco al cerrar", () => {
    render(<BancoPrueba />);
    const dialogo = abrir();
    expect(dialogo.hasAttribute("open")).toBe(true);
    expect(screen.getByRole("button", { name: "Ver 2 preguntas" })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Cerrar filtros" }));
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(document.activeElement).toBe(screen.getByRole("button", { name: "Abrir filtros" }));
  });

  it("mantiene la selección en borrador y la descarta al cancelar", () => {
    const onAplicar = vi.fn();
    render(<BancoPrueba onAplicar={onAplicar} />);
    abrir();
    elegirMadrid();

    expect(screen.getByRole("button", { name: "Ver 1 pregunta" })).toBeTruthy();
    expect(screen.getByTestId("filtros-aplicados").textContent).toBe("{}");
    fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(onAplicar).not.toHaveBeenCalled();

    abrir();
    expect(screen.getByRole("button", { name: "Ver 2 preguntas" })).toBeTruthy();
    expect(
      within(screen.getByRole("region", { name: "Región" }))
        .getByRole("button", { name: /Madrid/ })
        .getAttribute("aria-pressed"),
    ).toBe("false");
  });

  it("aplica los filtros elegidos y restablece el borrador al reabrir", () => {
    const onAplicar = vi.fn();
    render(<BancoPrueba onAplicar={onAplicar} />);
    abrir();
    elegirMadrid();
    fireEvent.click(screen.getByRole("button", { name: "Ver 1 pregunta" }));

    expect(onAplicar).toHaveBeenCalledWith({ region: ["Madrid"] });
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(screen.getByTestId("filtros-aplicados").textContent).toBe('{"region":["Madrid"]}');

    abrir();
    expect(
      within(screen.getByRole("region", { name: "Región" }))
        .getByRole("button", { name: /Madrid/ })
        .getAttribute("aria-pressed"),
    ).toBe("true");
  });

  it("limpia solo el borrador hasta aplicar", () => {
    const onAplicar = vi.fn();
    render(<BancoPrueba inicial={{ region: ["Madrid"] }} onAplicar={onAplicar} />);
    abrir();
    fireEvent.click(screen.getByRole("button", { name: "Limpiar filtros (1)" }));
    expect(screen.getByRole("button", { name: "Ver 2 preguntas" })).toBeTruthy();
    expect(screen.getByTestId("filtros-aplicados").textContent).toBe('{"region":["Madrid"]}');
    fireEvent.click(screen.getByRole("button", { name: "Ver 2 preguntas" }));
    expect(onAplicar).toHaveBeenCalledWith({});
  });

  it("cierra con Escape o al pulsar el fondo sin aplicar", () => {
    const onAplicar = vi.fn();
    render(<BancoPrueba onAplicar={onAplicar} />);
    const dialogo = abrir();
    elegirMadrid();
    fireEvent(dialogo, new Event("cancel", { cancelable: true }));
    expect(screen.queryByRole("dialog")).toBeNull();

    const reabierto = abrir();
    fireEvent.click(reabierto);
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(onAplicar).not.toHaveBeenCalled();
  });
});

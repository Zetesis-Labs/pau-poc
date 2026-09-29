// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { BotonTema } from "./BotonTema";

function simularSistema(oscuro: boolean) {
  const media = Object.assign(new EventTarget(), {
    matches: oscuro,
    media: "(prefers-color-scheme: dark)",
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
  });
  vi.stubGlobal("matchMedia", () => media as MediaQueryList);

  return {
    cambiar(oscuroAhora: boolean) {
      media.matches = oscuroAhora;
      media.dispatchEvent(new Event("change"));
    },
  };
}

const selector = () => screen.getByRole("combobox", { name: "Tema" }) as HTMLSelectElement;

beforeEach(() => {
  localStorage.clear();
  delete document.documentElement.dataset.tema;
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  localStorage.clear();
  delete document.documentElement.dataset.tema;
});

describe("BotonTema", () => {
  it("sin preferencia guardada sigue los cambios del sistema en vivo", () => {
    const sistema = simularSistema(false);
    render(<BotonTema />);

    expect(selector().value).toBe("sistema");
    expect(document.documentElement.dataset.tema).toBe("claro");
    sistema.cambiar(true);
    expect(document.documentElement.dataset.tema).toBe("oscuro");
    sistema.cambiar(false);
    expect(document.documentElement.dataset.tema).toBe("claro");
  });

  it("la selección manual se guarda y prevalece sobre el sistema", () => {
    const sistema = simularSistema(false);
    const vista = render(<BotonTema />);
    fireEvent.change(selector(), { target: { value: "oscuro" } });

    expect(localStorage.getItem("pau-tema")).toBe("oscuro");
    expect(document.documentElement.dataset.tema).toBe("oscuro");
    sistema.cambiar(true);
    sistema.cambiar(false);
    expect(document.documentElement.dataset.tema).toBe("oscuro");

    vista.unmount();
    render(<BotonTema />);
    expect(selector().value).toBe("oscuro");
    expect(document.documentElement.dataset.tema).toBe("oscuro");
  });

  it("volver a Sistema borra la preferencia y vuelve a seguir el sistema", () => {
    localStorage.setItem("pau-tema", "oscuro");
    const sistema = simularSistema(false);
    render(<BotonTema />);
    expect(document.documentElement.dataset.tema).toBe("oscuro");

    fireEvent.change(selector(), { target: { value: "sistema" } });
    expect(localStorage.getItem("pau-tema")).toBeNull();
    expect(document.documentElement.dataset.tema).toBe("claro");
    sistema.cambiar(true);
    expect(document.documentElement.dataset.tema).toBe("oscuro");
  });

  it("funciona durante la visita aunque el almacenamiento esté bloqueado", () => {
    const sistema = simularSistema(true);
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("Almacenamiento bloqueado");
    });
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("Almacenamiento bloqueado");
    });
    vi.spyOn(Storage.prototype, "removeItem").mockImplementation(() => {
      throw new Error("Almacenamiento bloqueado");
    });
    render(<BotonTema />);

    expect(document.documentElement.dataset.tema).toBe("oscuro");
    fireEvent.change(selector(), { target: { value: "claro" } });
    expect(document.documentElement.dataset.tema).toBe("claro");
    sistema.cambiar(false);
    sistema.cambiar(true);
    expect(document.documentElement.dataset.tema).toBe("claro");

    fireEvent.change(selector(), { target: { value: "sistema" } });
    expect(document.documentElement.dataset.tema).toBe("oscuro");
    sistema.cambiar(false);
    expect(document.documentElement.dataset.tema).toBe("claro");
  });
});

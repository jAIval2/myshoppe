"use client";
import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useRef,
  type ReactNode,
} from "react";
import {
  api,
  json,
  type Cart,
  type Session,
  type Product,
  type Variant,
} from "@/lib/api";
import { Dialog, ErrorMessage } from "./ui";
import { VariantPicker } from "./variant-picker";

type Shop = {
  cart: Cart;
  saved: Set<string>;
  session: Session | null;
  refresh: () => Promise<void>;
  changeQuantity: (id: string, quantity: number) => Promise<void>;
  save: (id: string) => Promise<void>;
  quickAdd: (product: Product) => void;
  notify: (message: string) => void;
};
const Context = createContext<Shop | null>(null);
export const useShop = () => {
  const value = useContext(Context);
  if (!value) throw new Error("ShopProvider missing");
  return value;
};
export function ShopProvider({ children }: { children: ReactNode }) {
  const [cart, setCart] = useState<Cart>({
    version: 1,
    items: [],
    subtotal: 0,
    count: 0,
  });
  const [saved, setSaved] = useState(new Set<string>());
  const [session, setSession] = useState<Session | null>(null);
  const [product, setProduct] = useState<Product | null>(null);
  const [notice, notify] = useState("");
  const [error, setError] = useState<unknown>(null);
  const refreshing = useRef<Promise<void> | null>(null);
  const sessionInit = useRef<Promise<Session> | null>(null);
  const ensureSession = useCallback(() => {
    if (!sessionInit.current) {
      sessionInit.current = api<Session>("/session", { method: "POST" })
        .then((user) => {
          setSession(user);
          return user;
        })
        .finally(() => {
          sessionInit.current = null;
        });
    }
    return sessionInit.current;
  }, []);
  const refresh = useCallback(() => {
    if (refreshing.current) return refreshing.current;
    refreshing.current = (async () => {
      // Anonymous reads are stateless; the first mutation establishes a guest session.
      const user = await api<Session>("/session");
      setSession(user);
      const [bag, favourites] = await Promise.all([
        api<Cart>("/cart"),
        api<Product[]>("/favourites"),
      ]);
      setCart(bag);
      setSaved(new Set(favourites.map((p) => p.id)));
    })().finally(() => {
      refreshing.current = null;
    });
    return refreshing.current;
  }, []);
  useEffect(() => {
    refresh().catch(setError);
  }, [refresh]);
  useEffect(() => {
    if (!notice) return;
    const timer = setTimeout(() => notify(""), 3500);
    return () => clearTimeout(timer);
  }, [notice]);
  const changeQuantity = async (id: string, quantity: number) => {
    try {
      await ensureSession();
      setCart(
        await api<Cart>(
          "/cart/items",
          json("PUT", {
            variant_id: id,
            quantity,
            expected_version: cart.version,
          }),
        ),
      );
    } catch (error) {
      await refresh();
      throw error;
    }
  };
  const save = async (id: string) => {
    await ensureSession();
    await api(`/favourites/${id}`, json(saved.has(id) ? "DELETE" : "PUT"));
    setSaved((old) => {
      const next = new Set(old);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };
  const add = async (variant: Variant) => {
    await changeQuantity(
      variant.id,
      (cart.items.find((i) => i.variant_id === variant.id)?.quantity || 0) + 1,
    );
    setProduct(null);
    notify("Added to your bag");
  };
  return (
    <Context.Provider
      value={{
        cart,
        saved,
        session,
        refresh,
        changeQuantity,
        save,
        quickAdd: setProduct,
        notify,
      }}
    >
      {children}
      <Dialog
        open={!!product}
        onClose={() => setProduct(null)}
        title="Choose your options"
        className="quick-add-dialog"
      >
        {product && (
          <>
            <h2>{product.title}</h2>
            <VariantPicker product={product} onAdd={add} />
          </>
        )}
      </Dialog>
      {notice && (
        <div className="toast" role="status">
          {notice}
        </div>
      )}
      {!!error && (
        <div className="connection-message">
          <ErrorMessage error={error} />
          <button
            onClick={() => {
              setError(null);
              refresh().catch(setError);
            }}
          >
            Retry connection
          </button>
        </div>
      )}
    </Context.Provider>
  );
}

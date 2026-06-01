export function Spinner({ size = 18 }: { size?: number }) {
  return (
    <span
      style={{ width: size, height: size }}
      className="inline-block rounded-full border-2 border-gray-200 border-t-azul-acento animate-spin"
    />
  )
}

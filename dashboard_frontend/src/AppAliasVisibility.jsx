
export function AliasVisibility({data}){
  return(
    <div className="aliases-panel">
      <h3 className="panel-title">Aliases</h3>
      {Object.keys(data).length === 0 ? (
        <p className="empty-note">No aliases created</p>
        ) : (
          <ul className="alias-list">
            {Object.entries(data).map(([alias, commands]) => (
              <li key={alias} className="alias-item">
                <span className="alias-name">
                  {alias.charAt(0).toUpperCase() + alias.slice(1)}
                </span>
                <span className="alias-arrow">→</span>
                <span className="alias-targets">
                  {commands
                    .map((cmd) =>
                      cmd.target.charAt(0).toUpperCase() + cmd.target.slice(1)
                    )
                    .join(", ")}
                </span>
              </li>
            ))}
          </ul>
        )}
    </div>
  )
}


export default function AppAliasVisibility({aliases}){
    return(
        <AliasVisibility
          data={aliases}
        />
    )
}